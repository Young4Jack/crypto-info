package com.example.pricemonitor

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.LinearLayout
import android.widget.TextView
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.util.Timer
import java.util.TimerTask
import java.util.concurrent.TimeUnit

class FloatingWindowService : Service() {

    companion object {
        const val API_URL = "https://pm.jack2u.com/api/watchlist/public"
        const val TAG = "FloatingWindowService"
        const val PREFS_NAME = "price_monitor_prefs"

        const val ACTION_UPDATE_SETTINGS = "com.example.pricemonitor.UPDATE_SETTINGS"

        const val EXTRA_KEEP_SCREEN_ON = "keep_screen_on"
        const val EXTRA_SHOW_FLOAT_TOGGLE = "show_float_toggle"
        const val EXTRA_SHOW_CLOSE_BTN = "show_close_btn"
        const val EXTRA_REFRESH_INTERVAL = "refresh_interval"

        const val DEFAULT_REFRESH_INTERVAL = 3000L
    }

    private lateinit var prefs: SharedPreferences

    private lateinit var windowManager: WindowManager
    private lateinit var floatingView: View
    private lateinit var layoutParams: WindowManager.LayoutParams
    private lateinit var priceContainer: LinearLayout
    private lateinit var floatToggleContainer: LinearLayout
    private lateinit var btnFloatKeepScreen: TextView
    private lateinit var btnClose: TextView

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()

    private val mainHandler = Handler(Looper.getMainLooper())
    private var timer: Timer? = null

    private var initialX = 0
    private var initialY = 0
    private var initialTouchX = 0f
    private var initialTouchY = 0f
    private var isDragging = false

    private val lastPrices = mutableMapOf<String, Double>()

    // 当前设置
    private var isKeepScreenOn = false
    private var isShowFloatToggle = false
    private var isShowCloseBtn = true
    private var refreshInterval = DEFAULT_REFRESH_INTERVAL

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        
        // 从 SharedPreferences 加载设置
        loadSettings()
        
        initFloatingWindow()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_UPDATE_SETTINGS) {
            // 接收更新设置
            isKeepScreenOn = intent.getBooleanExtra(EXTRA_KEEP_SCREEN_ON, isKeepScreenOn)
            isShowFloatToggle = intent.getBooleanExtra(EXTRA_SHOW_FLOAT_TOGGLE, isShowFloatToggle)
            isShowCloseBtn = intent.getBooleanExtra(EXTRA_SHOW_CLOSE_BTN, isShowCloseBtn)
            val newInterval = intent.getLongExtra(EXTRA_REFRESH_INTERVAL, refreshInterval / 1000)
            refreshInterval = newInterval * 1000

            // 保存到 SharedPreferences
            saveSettings()

            applyKeepScreenFlag()
            updateFloatToggleVisibility()
            updateCloseBtnVisibility()
            restartTimer()
        }
        // 确保首次启动时也启动定时器
        if (::floatingView.isInitialized && timer == null) {
            startPriceTimer()
        }
        return START_NOT_STICKY
    }

    private fun loadSettings() {
        isKeepScreenOn = prefs.getBoolean("keep_screen_on", false)
        isShowFloatToggle = prefs.getBoolean("show_float_toggle", false)
        isShowCloseBtn = prefs.getBoolean("show_close_btn", true)
        val intervalSec = prefs.getInt("refresh_interval", 3)
        refreshInterval = intervalSec * 1000L
        Log.d(TAG, "加载设置: keepScreen=$isKeepScreenOn, showFloat=$isShowFloatToggle, showClose=$isShowCloseBtn, interval=$refreshInterval")
    }

    private fun saveSettings() {
        prefs.edit()
            .putBoolean("keep_screen_on", isKeepScreenOn)
            .putBoolean("show_float_toggle", isShowFloatToggle)
            .putBoolean("show_close_btn", isShowCloseBtn)
            .putInt("refresh_interval", (refreshInterval / 1000).toInt())
            .apply()
    }

    private fun initFloatingWindow() {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        floatingView = LayoutInflater.from(this).inflate(R.layout.layout_floating_window, null)
        priceContainer = floatingView.findViewById(R.id.priceContainer)
        floatToggleContainer = floatingView.findViewById(R.id.floatToggleContainer)
        btnFloatKeepScreen = floatingView.findViewById(R.id.btnFloatKeepScreen)
        btnClose = floatingView.findViewById(R.id.btnClose)

        layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 30
            y = 100
        }

        try {
            windowManager.addView(floatingView, layoutParams)
        } catch (e: Exception) {
            Log.e(TAG, "添加悬浮窗失败: ${e.message}")
        }

        setupDrag()

        // 悬浮窗常亮按钮点击
        btnFloatKeepScreen.setOnClickListener {
            isKeepScreenOn = !isKeepScreenOn
            saveSettings()
            applyKeepScreenFlag()
            btnFloatKeepScreen.text = if (isKeepScreenOn) "☀ 常亮开" else "☀ 常亮关"
        }

        // 关闭按钮
        btnClose.setOnClickListener {
            stopSelf()
        }

        // 应用设置
        applyKeepScreenFlag()
        updateFloatToggleVisibility()
        updateCloseBtnVisibility()
    }

    private fun setupDrag() {
        floatingView.setOnTouchListener(object : View.OnTouchListener {
            override fun onTouch(v: View?, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        isDragging = false
                        initialX = layoutParams.x
                        initialY = layoutParams.y
                        initialTouchX = event.rawX
                        initialTouchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val deltaX = event.rawX - initialTouchX
                        val deltaY = event.rawY - initialTouchY
                        if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
                            isDragging = true
                        }
                        layoutParams.x = (initialX + deltaX).toInt()
                        layoutParams.y = (initialY + deltaY).toInt()
                        windowManager.updateViewLayout(floatingView, layoutParams)
                        return true
                    }
                    MotionEvent.ACTION_UP -> {
                        return isDragging
                    }
                }
                return false
            }
        })
    }

    private fun startPriceTimer() {
        timer = Timer()
        timer?.schedule(object : TimerTask() {
            override fun run() {
                fetchPrice()
            }
        }, 0, refreshInterval)
    }

    private fun restartTimer() {
        timer?.cancel()
        startPriceTimer()
    }

    private fun fetchPrice() {
        val apiUrl = prefs.getString("api_url", API_URL) ?: API_URL
        val request = Request.Builder()
            .url(apiUrl)
            .get()
            .build()

        try {
            val response = okHttpClient.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string()
                if (body != null) {
                    val jsonArray = JSONArray(body)
                    val priceList = mutableListOf<Triple<String, String, Double>>()
                    for (i in 0 until jsonArray.length()) {
                        val item = jsonArray.getJSONObject(i)
                        val symbol = item.optString("crypto_symbol", "")
                        val name = item.optString("crypto_name", "")
                        val price = item.optDouble("current_price", 0.0)
                        priceList.add(Triple(symbol, name, price))
                    }
                    mainHandler.post {
                        updatePriceList(priceList)
                    }
                }
            } else {
                Log.e(TAG, "请求失败: ${response.code}")
            }
            response.close()
        } catch (e: Exception) {
            Log.e(TAG, "网络请求异常: ${e.message}")
        }
    }

    private fun updatePriceList(priceList: List<Triple<String, String, Double>>) {
        priceContainer.removeAllViews()
        for ((symbol, name, price) in priceList) {
            val lastPrice = lastPrices[symbol]
            val color = when {
                lastPrice == null -> 0xBAFFFFFF.toInt()
                price > lastPrice -> 0xBAFF4444.toInt()
                price < lastPrice -> 0xBA44FF44.toInt()
                else -> 0xBAFFFFFF.toInt()
            }
            lastPrices[symbol] = price

            val itemLayout = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(4, 5, 4, 5)
                gravity = android.view.Gravity.CENTER
            }

            val priceText = TextView(this).apply {
                text = "$price"
                textSize = 12f
                setTextColor(color)
                typeface = Typeface.DEFAULT_BOLD
                setPadding(0, 10, 0, 0)
                gravity = android.view.Gravity.CENTER
            }

            val nameText = TextView(this).apply {
                text = "[$name]"
                textSize = 6f
                setTextColor(0xBAFFFFFF.toInt())
                setPadding(0, 8, 0, 0)
                gravity = android.view.Gravity.CENTER
            }

            itemLayout.addView(priceText)
            itemLayout.addView(nameText)
            priceContainer.addView(itemLayout)
        }
    }

    // 应用常亮标志
    private fun applyKeepScreenFlag() {
        if (::layoutParams.isInitialized) {
            if (isKeepScreenOn) {
                layoutParams.flags = layoutParams.flags or WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            } else {
                layoutParams.flags = layoutParams.flags and WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON.inv()
            }
            windowManager.updateViewLayout(floatingView, layoutParams)
        }
    }

    // 更新悬浮窗常亮按钮显隐
    private fun updateFloatToggleVisibility() {
        if (::floatToggleContainer.isInitialized) {
            floatToggleContainer.visibility = if (isShowFloatToggle) View.VISIBLE else View.GONE
            btnFloatKeepScreen.text = if (isKeepScreenOn) "☀ 常亮开" else "☀ 常亮关"
        }
    }

    // 更新关闭按钮显隐
    private fun updateCloseBtnVisibility() {
        if (::btnClose.isInitialized) {
            btnClose.visibility = if (isShowCloseBtn) View.VISIBLE else View.GONE
        }
    }

    private fun stopPriceTimer() {
        timer?.cancel()
        timer = null
    }

    override fun onDestroy() {
        super.onDestroy()
        stopPriceTimer()
        if (::floatingView.isInitialized) {
            windowManager.removeView(floatingView)
        }
    }
}
