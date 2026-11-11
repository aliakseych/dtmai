import SwiftUI
import WidgetKit

private let appGroup = "group.uz.dtmai.app"

struct StreakEntry: TimelineEntry {
    let date: Date
    let streak: Int
    let dailyXp: Int
    let dailyGoal: Int
}

struct StreakProvider: TimelineProvider {
    func placeholder(in context: Context) -> StreakEntry {
        StreakEntry(date: Date(), streak: 7, dailyXp: 20, dailyGoal: 50)
    }

    func getSnapshot(in context: Context, completion: @escaping (StreakEntry) -> Void) {
        completion(load())
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<StreakEntry>) -> Void) {
        completion(Timeline(entries: [load()], policy: .after(Date().addingTimeInterval(30 * 60))))
    }

    private func load() -> StreakEntry {
        let d = UserDefaults(suiteName: appGroup)
        let goal = d?.integer(forKey: "daily_goal") ?? 0
        return StreakEntry(
            date: Date(),
            streak: d?.integer(forKey: "streak") ?? 0,
            dailyXp: d?.integer(forKey: "daily_xp") ?? 0,
            dailyGoal: goal > 0 ? goal : 50
        )
    }
}

struct StreakWidgetView: View {
    let entry: StreakEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Text("🔥").font(.system(size: 28))
                Text("\(entry.streak)")
                    .font(.system(size: 30, weight: .heavy, design: .rounded))
                    .foregroundColor(Color(red: 1, green: 0.588, blue: 0))
            }
            ProgressView(value: Double(min(entry.dailyXp, entry.dailyGoal)), total: Double(entry.dailyGoal))
                .tint(Color(red: 0.345, green: 0.8, blue: 0.008))
            Text("\(entry.dailyXp) / \(entry.dailyGoal) XP")
                .font(.system(size: 13, weight: .bold, design: .rounded))
                .foregroundColor(Color(white: 0.29))
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .containerBackground(.white, for: .widget)
    }
}

@main
struct StreakWidget: Widget {
    let kind = "StreakWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: StreakProvider()) { entry in
            StreakWidgetView(entry: entry)
        }
        .configurationDisplayName("DTM AI")
        .description("Streak and daily goal")
        .supportedFamilies([.systemSmall])
    }
}
