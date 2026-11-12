import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/api/api.dart';
import 'core/api/api_client.dart';
import 'core/l10n_ext.dart';
import 'core/models.dart';
import 'features/auth/auth_providers.dart';
import 'features/auth/login_screen.dart';
import 'features/learn/learn_screen.dart';
import 'features/leagues/leagues_screen.dart';
import 'features/lesson/done_screen.dart';
import 'features/lesson/lesson_screen.dart';
import 'features/lyceums/lyceums_screen.dart';
import 'features/mocks/mock_result_screen.dart';
import 'features/mocks/mock_runner_screen.dart';
import 'features/mocks/mocks_screen.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/profile/notification_settings_screen.dart';
import 'features/practice/practice_screen.dart';
import 'features/premium/premium_screen.dart';
import 'features/profile/profile_providers.dart';
import 'features/profile/profile_screen.dart';
import 'features/quests/quests_screen.dart';
import 'theme/tokens.dart';
import 'widgets/mascot.dart';

/// Guest-first: on first launch (no stored tokens) a guest account is created.
/// Holds the last bootstrap error so the splash can offer a retry.
class GuestBootstrap extends Notifier<Object?> {
  bool _running = false;

  @override
  Object? build() => null;

  Future<void> run() async {
    if (_running) return;
    _running = true;
    state = null;
    try {
      final tokens = await ref.read(apiProvider).guest();
      await ref.read(authProvider.notifier).signIn(tokens, account: false);
    } catch (e) {
      state = e;
    } finally {
      _running = false;
    }
  }
}

final guestBootstrapProvider = NotifierProvider<GuestBootstrap, Object?>(GuestBootstrap.new);

final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(authProvider, (_, next) {
    refresh.value++;
    // A real account whose session ended goes to sign-in; only first launch / guests get a new guest.
    if (next == AuthStatus.signedOut && !ref.read(authProvider.notifier).hadAccount) {
      ref.read(guestBootstrapProvider.notifier).run();
    }
  });
  ref.listen(meProvider, (_, _) => refresh.value++);
  ref.listen(onboardingSkippedProvider, (_, _) => refresh.value++);
  ref.onDispose(refresh.dispose);

  String? redirect(BuildContext context, GoRouterState state) {
    final loc = state.matchedLocation;
    switch (ref.read(authProvider)) {
      case AuthStatus.unknown:
        return loc == '/splash' ? null : '/splash';
      case AuthStatus.signedOut:
        // Real account signed out / expired: sign-in. Otherwise the guest account is being created.
        if (ref.read(authProvider.notifier).hadAccount) return loc == '/login' ? null : '/login';
        return (loc == '/splash' || loc == '/login') ? null : '/splash';
      case AuthStatus.signedIn:
        final me = ref.read(meProvider);
        final m = me.value;
        if (m == null) {
          if (me.hasError) return (loc == '/splash') ? '/learn' : null;
          return loc == '/splash' ? null : '/splash';
        }
        final needsOnboarding =
            m.educationLanguageId == null && m.dreamLyceumIds.isEmpty && !ref.read(onboardingSkippedProvider);
        if (needsOnboarding) {
          return (loc == '/onboarding' || loc == '/login' || loc.startsWith('/session/')) ? null : '/onboarding';
        }
        if (loc == '/splash' || loc == '/onboarding') return '/learn';
        return null;
    }
  }

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: redirect,
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const _Splash()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/onboarding', builder: (_, _) => const OnboardingScreen()),
      GoRoute(
        path: '/session/:mode/:id',
        builder: (_, s) => LessonScreen(
          mode: s.pathParameters['mode']!,
          refId: s.pathParameters['id'],
          topicId: s.uri.queryParameters['topic'],
          typeId: s.uri.queryParameters['type'],
        ),
      ),
      GoRoute(
        path: '/done',
        redirect: (_, s) => s.extra is FinishResult ? null : '/learn',
        builder: (_, s) => DoneScreen(result: s.extra! as FinishResult),
      ),
      GoRoute(path: '/mocks/run/:id', builder: (_, s) => MockRunnerScreen(blueprintId: s.pathParameters['id']!)),
      GoRoute(
        path: '/mocks/result/:id',
        builder: (_, s) => MockResultScreen(attemptId: s.pathParameters['id']!, result: s.extra as AttemptResult?),
      ),
      GoRoute(path: '/settings/notifications', builder: (_, _) => const NotificationSettingsScreen()),
      GoRoute(path: '/premium', builder: (_, _) => const PremiumScreen()),
      GoRoute(path: '/quests', builder: (_, _) => const QuestsScreen()),
      GoRoute(path: '/lyceums', builder: (_, _) => const LyceumsScreen()),
      StatefulShellRoute.indexedStack(
        builder: (_, _, shell) => _Shell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [GoRoute(path: '/learn', builder: (_, _) => const LearnScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/practice', builder: (_, _) => const PracticeScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/mocks', builder: (_, _) => const MocksScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/leagues', builder: (_, _) => const LeaguesScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen())]),
        ],
      ),
    ],
  );
});

class _Splash extends ConsumerStatefulWidget {
  const _Splash();

  @override
  ConsumerState<_Splash> createState() => _SplashState();
}

class _SplashState extends ConsumerState<_Splash> {
  @override
  void initState() {
    super.initState();
    // Auth may already have resolved to signedOut before this screen existed.
    Future.microtask(() {
      if (mounted && ref.read(authProvider) == AuthStatus.signedOut && !ref.read(authProvider.notifier).hadAccount) {
        ref.read(guestBootstrapProvider.notifier).run();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final error = ref.watch(guestBootstrapProvider);
    final l = context.l10n;
    return Scaffold(
      body: Center(
        child: error == null
            ? const Mascot(size: 160)
            : Column(mainAxisSize: MainAxisSize.min, children: [
                const Mascot(pose: MascotPose.sad, size: 120),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(apiErrorMessage(error, l.errorGeneric), textAlign: TextAlign.center),
                ),
                FilledButton(onPressed: () => ref.read(guestBootstrapProvider.notifier).run(), child: Text(l.retry)),
              ]),
      ),
    );
  }
}

class _Shell extends StatelessWidget {
  const _Shell({required this.shell});
  final StatefulNavigationShell shell;

  static const _maxContentWidth = 720.0;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final items = [
      (Icons.home_rounded, l.learn),
      (Icons.fitness_center_rounded, l.practice),
      (Icons.assignment_rounded, l.mocks),
      (Icons.emoji_events_rounded, l.leagues),
      (Icons.person_rounded, l.profile),
    ];
    void select(int i) => shell.goBranch(i, initialLocation: i == shell.currentIndex);
    final wide = MediaQuery.sizeOf(context).width >= 600;
    final body = Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: _maxContentWidth), child: shell),
    );
    if (!wide) {
      return Scaffold(
        body: body,
        bottomNavigationBar: NavigationBar(
          selectedIndex: shell.currentIndex,
          onDestinationSelected: select,
          destinations: [for (final (icon, label) in items) NavigationDestination(icon: Icon(icon), label: label)],
        ),
      );
    }
    return Scaffold(
      body: Row(children: [
        NavigationRail(
          selectedIndex: shell.currentIndex,
          onDestinationSelected: select,
          labelType: NavigationRailLabelType.all,
          backgroundColor: Tokens.surface,
          indicatorColor: Tokens.accent,
          selectedIconTheme: const IconThemeData(color: Tokens.brand),
          leading: const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Mascot(size: 48)),
          destinations: [
            for (final (icon, label) in items) NavigationRailDestination(icon: Icon(icon), label: Text(label)),
          ],
        ),
        const VerticalDivider(width: 2),
        Expanded(child: body),
      ]),
    );
  }
}
