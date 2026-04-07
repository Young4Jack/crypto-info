package com.example.pricemonitor

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class FloatingWindowTileService : TileService() {

    private val PREFS_NAME = "price_monitor_prefs"
    private val KEY_MONITOR_ON = "monitor_on"

    override fun onStartListening() {
        super.onStartListening()
        updateTileState()
    }

    override fun onClick() {
        super.onClick()

        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val isOn = prefs.getBoolean(KEY_MONITOR_ON, false)

        if (isOn) {
            stopFloatingService()
            prefs.edit().putBoolean(KEY_MONITOR_ON, false).apply()
        } else {
            startFloatingService()
            prefs.edit().putBoolean(KEY_MONITOR_ON, true).apply()
        }

        updateTileState()
    }

    private fun updateTileState() {
        val tile = qsTile ?: return
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val isOn = prefs.getBoolean(KEY_MONITOR_ON, false)

        if (isOn) {
            tile.state = Tile.STATE_ACTIVE
            tile.label = "价格监控"
            tile.subtitle = "运行中"
        } else {
            tile.state = Tile.STATE_INACTIVE
            tile.label = "价格监控"
            tile.subtitle = "已停止"
        }
        tile.updateTile()
    }

    private fun startFloatingService() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val intent = Intent(this, FloatingWindowService::class.java).apply {
            putExtra(FloatingWindowService.EXTRA_KEEP_SCREEN_ON, prefs.getBoolean("keep_screen_on", false))
            putExtra(FloatingWindowService.EXTRA_SHOW_FLOAT_TOGGLE, prefs.getBoolean("show_float_toggle", false))
            putExtra(FloatingWindowService.EXTRA_REFRESH_INTERVAL, prefs.getInt("refresh_interval", 3).toLong())
        }
        startService(intent)
    }

    private fun stopFloatingService() {
        val intent = Intent(this, FloatingWindowService::class.java)
        stopService(intent)
    }
}
