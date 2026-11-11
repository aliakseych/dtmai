package uz.dtmai.app

import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.SharedPreferences
import android.widget.RemoteViews
import es.antonborri.home_widget.HomeWidgetProvider

/** Streak + daily goal widget. Data is written by the Flutter side through home_widget. */
class StreakWidgetProvider : HomeWidgetProvider() {
    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
        widgetData: SharedPreferences,
    ) {
        val streak = widgetData.getInt("streak", 0)
        val xp = widgetData.getInt("daily_xp", 0)
        val goal = widgetData.getInt("daily_goal", 50).coerceAtLeast(1)

        appWidgetIds.forEach { id ->
            val views = RemoteViews(context.packageName, R.layout.streak_widget).apply {
                setTextViewText(R.id.widget_streak, streak.toString())
                setTextViewText(R.id.widget_goal_text, "$xp / $goal XP")
                setProgressBar(R.id.widget_goal_bar, goal, xp.coerceAtMost(goal), false)
            }
            appWidgetManager.updateAppWidget(id, views)
        }
    }
}
