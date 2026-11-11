import 'package:flutter/material.dart';
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
  ref.listen(meProvider, (_, __) => refresh.value++);
  ref.listen(onboardingSkippedProvider, (_, __) => refresh.value++);
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
            m.educationLanguageId == null && m.targetLyceumId == null && !ref.read(onboardingSkippedProvider);
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
      GoRoute(path: '/splash', builder: (_, __) => const _Splash()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingScreen()),
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
      GoRoute(path: '/settings/notifications', builder: (_, __) => const NotificationSettingsScreen()),
      GoRoute(path: '/premium', builder: (_, __) => const PremiumScreen()),
      GoRoute(path: '/quests', builder: (_, __) => const QuestsScreen()),
      GoRoute(path: '/lyceums', builder: (_, __) => const LyceumsScreen()),
      StatefulShellRoute.indexedStack(
        builder: (_, __, shell) => _Shell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [GoRoute(path: '/learn', builder: (_, __) => const LearnScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/practice', builder: (_, __) => const PracticeScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/mocks', builder: (_, __) => const MocksScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/leagues', builder: (_, __) => const LeaguesScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen())]),
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

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: shell.currentIndex,
        onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.home_rounded), label: l.learn),
          NavigationDestination(icon: const Icon(Icons.fitness_center_rounded), label: l.practice),
          NavigationDestination(icon: const Icon(Icons.assignment_rounded), label: l.mocks),
          NavigationDestination(icon: const Icon(Icons.emoji_events_rounded), label: l.leagues),
          NavigationDestination(icon: const Icon(Icons.person_rounded), label: l.profile),
        ],
      ),
    );
  }
}
