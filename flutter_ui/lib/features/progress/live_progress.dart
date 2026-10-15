import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

/// 기능별 맞춤 진행 화면(알파, 2026-10-15, docs/PROGRESS_FLOW_DESIGN.md).
///
/// iPhone의 다이내믹 아일랜드·활동 링·부드러운 스프링 전환을 빌려, 지금 무엇을 하는지 한눈에 보이고
/// 기다리는 동안 지루하지 않게 한다. 색·모서리·글꼴은 앱의 다른 화면(main.dart 팔레트)과 같다.
/// 엔진이 1초마다 보내는 `live` 값(progress_guide.progress_view)을 그대로 그리며, 숫자·링·단계는
/// 값 사이를 애니메이션으로 이어 준다. 시스템의 '동작 줄이기'가 켜져 있으면 반복 애니메이션을 끈다.
class LiveProgress extends StatefulWidget {
  const LiveProgress({super.key, required this.live, required this.onShowLog});

  final Map live;
  final VoidCallback onShowLog;

  @override
  State<LiveProgress> createState() => _LiveProgressState();
}

// main.dart와 같은 팔레트.
const _ink = Color(0xff172b4d);
const _muted = Color(0xff64748b);
const _faint = Color(0xff8b98ad);
const _line = Color(0xffe2e8f0);
const _blue = Color(0xff2563eb);
const _blueDeep = Color(0xff1d4ed8);
const _blueSoft = Color(0xffedf3ff);
const _sky = Color(0xff60a5fa);
const _mint = Color(0xff287c72);
const _mintBright = Color(0xff34c79a);
const _mintSoft = Color(0xffdff3ee);
const _red = Color(0xffdc2626);
const _island = Color(0xff0f172a);

/// iOS 느낌의 탄성 곡선(살짝 넘쳤다가 제자리).
const _spring = Curves.easeOutBack;

IconData _modeIcon(String icon) => switch (icon) {
  'spacing' => Icons.space_bar_rounded,
  'unify' => Icons.rule_rounded,
  'convert' => Icons.swap_horiz_rounded,
  _ => Icons.auto_awesome_rounded,
};

String _clock(int seconds) {
  final m = seconds ~/ 60;
  final s = seconds % 60;
  return m > 0 ? '$m분 ${s.toString().padLeft(2, '0')}초' : '$s초';
}

class _LiveProgressState extends State<LiveProgress>
    with TickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1600),
  );
  late final AnimationController _spin = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 2400),
  );
  Timer? _ticker;
  int _tip = 0;
  int _tipTicks = 0;
  int _elapsedBase = 0;
  DateTime _elapsedAt = DateTime.now();
  bool _reduceMotion = false;

  Map get live => widget.live;
  bool get running => live['running'] == true;
  bool get finished => live['finished'] == true;
  List get steps => live['steps'] as List? ?? const [];
  List get queue => live['queue'] as List? ?? const [];
  List get tips => live['tips'] as List? ?? const [];
  Map get doc => live['doc'] as Map? ?? const {};
  bool get isConversion => live['mode'] == 'file_format';

  @override
  void initState() {
    super.initState();
    _syncElapsed();
    // 1초마다 경과 시간을 올리고, 6초마다 안내 문구를 바꾼다.
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() {
        if (running && tips.length > 1 && ++_tipTicks >= 6) {
          _tipTicks = 0;
          _tip = (_tip + 1) % tips.length;
        }
      });
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduceMotion = MediaQuery.maybeDisableAnimationsOf(context) ?? false;
    _syncMotion();
  }

  @override
  void didUpdateWidget(LiveProgress oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.live['elapsed'] != live['elapsed']) _syncElapsed();
    _syncMotion();
  }

  void _syncElapsed() {
    _elapsedBase = (live['elapsed'] as num?)?.toInt() ?? 0;
    _elapsedAt = DateTime.now();
  }

  void _syncMotion() {
    if (running && !_reduceMotion) {
      if (!_pulse.isAnimating) _pulse.repeat(reverse: true);
      if (!_spin.isAnimating) _spin.repeat();
    } else {
      _pulse.stop();
      _spin.stop();
    }
  }

  int get _elapsed => running
      ? _elapsedBase + DateTime.now().difference(_elapsedAt).inSeconds
      : _elapsedBase;

  Duration _d(int ms) =>
      _reduceMotion ? Duration.zero : Duration(milliseconds: ms);

  @override
  void dispose() {
    _ticker?.cancel();
    _pulse.dispose();
    _spin.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final wide = constraints.maxWidth >= 760;
      final hero = _hero();
      final detail = isConversion || steps.isEmpty ? _fileQueue() : _timeline();
      final footer = _footer();
      if (!wide) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [hero, const SizedBox(height: 24), detail, footer],
        );
      }
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 300, child: hero),
              const SizedBox(width: 32),
              Expanded(child: detail),
            ],
          ),
          footer,
        ],
      );
    },
  );

  // ---- 왼쪽: 아일랜드 + 활동 링 + 안내 ------------------------------------

  Widget _hero() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Align(child: _islandPill()),
      const SizedBox(height: 24),
      Center(child: _ring()),
      const SizedBox(height: 20),
      _badgeRow(),
      if (running && tips.isNotEmpty) ...[
        const SizedBox(height: 20),
        _tipCard(),
      ],
    ],
  );

  /// 다이내믹 아일랜드처럼 지금 단계를 알려 주는 검은 알약. 내용이 바뀌면 폭이 부드럽게 늘고 준다.
  Widget _islandPill() {
    final total = (doc['total'] as num?)?.toInt() ?? 0;
    final index = (doc['index'] as num?)?.toInt() ?? 0;
    final now = '${live['now'] ?? ''}';
    final label = finished
        ? '완료'
        : running
        ? (now.isEmpty ? '준비 중' : now)
        : '대기 중';
    return Semantics(
      liveRegion: true,
      label: '지금 단계: $label',
      child: AnimatedContainer(
        duration: _d(420),
        curve: _spring,
        padding: const EdgeInsets.fromLTRB(10, 8, 16, 8),
        decoration: BoxDecoration(
          color: _island,
          borderRadius: BorderRadius.circular(999),
          boxShadow: [
            BoxShadow(
              color: _island.withValues(alpha: running ? 0.22 : 0.08),
              blurRadius: running ? 22 : 10,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: AnimatedSize(
          duration: _d(420),
          curve: _spring,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _islandDot(),
              const SizedBox(width: 10),
              AnimatedSwitcher(
                duration: _d(360),
                transitionBuilder: (child, animation) => FadeTransition(
                  opacity: animation,
                  child: SlideTransition(
                    position: Tween(
                      begin: const Offset(0, 0.6),
                      end: Offset.zero,
                    ).animate(
                      CurvedAnimation(parent: animation, curve: _spring),
                    ),
                    child: child,
                  ),
                ),
                child: Text(
                  label,
                  key: ValueKey(label),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              if (total > 1 && index > 0 && !finished) ...[
                const SizedBox(width: 12),
                Text(
                  '$index/$total',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.6),
                    fontSize: 13,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _islandDot() {
    if (finished) {
      return _popIn(
        const CircleAvatar(
          radius: 9,
          backgroundColor: _mintBright,
          child: Icon(Icons.check_rounded, size: 13, color: Colors.white),
        ),
      );
    }
    final color = running ? _mintBright : _faint;
    return AnimatedBuilder(
      animation: _pulse,
      builder: (context, _) {
        final t = running ? Curves.easeInOut.transform(_pulse.value) : 0.0;
        return SizedBox(
          width: 18,
          height: 18,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 10 + 8 * t,
                height: 10 + 8 * t,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: color.withValues(alpha: 0.35 * (1 - t)),
                ),
              ),
              Container(
                width: 9,
                height: 9,
                decoration: BoxDecoration(shape: BoxShape.circle, color: color),
              ),
            ],
          ),
        );
      },
    );
  }

  /// Apple Watch 활동 링처럼 전체 진행을 채운다. 작업 중에는 끝점이 빛나며 숨을 쉰다.
  Widget _ring() {
    final ratio = ((live['ratio'] as num?)?.toDouble() ?? 0).clamp(0.0, 1.0);
    final caption = isConversion
        ? '파일 ${queue.where((f) => f['state'] == 'done' || f['state'] == 'failed').length}/${queue.length}'
        : steps.isEmpty
        ? ''
        : '단계 ${steps.where((s) => s['state'] == 'done').length}/${steps.length}';
    return TweenAnimationBuilder<double>(
      tween: Tween(end: ratio),
      duration: _d(900),
      curve: Curves.easeOutCubic,
      builder: (context, value, _) => AnimatedBuilder(
        animation: Listenable.merge([_pulse, _spin]),
        builder: (context, _) => SizedBox(
          width: 188,
          height: 188,
          child: CustomPaint(
            painter: _RingPainter(
              value: value,
              glow: running ? _pulse.value : 0,
              spin: running && value < 0.02 ? _spin.value : null,
              done: finished,
            ),
            child: Center(
              child: AnimatedSwitcher(
                duration: _d(500),
                transitionBuilder: (child, animation) => ScaleTransition(
                  scale: CurvedAnimation(
                    parent: animation,
                    curve: Curves.elasticOut,
                  ),
                  child: FadeTransition(opacity: animation, child: child),
                ),
                child: finished
                    ? const Icon(
                        Icons.check_rounded,
                        key: ValueKey('done'),
                        size: 72,
                        color: _mint,
                      )
                    : Column(
                        key: const ValueKey('count'),
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${(value * 100).round()}%',
                            style: const TextStyle(
                              fontSize: 40,
                              fontWeight: FontWeight.w800,
                              color: _ink,
                              letterSpacing: -1,
                              fontFeatures: [FontFeature.tabularFigures()],
                            ),
                          ),
                          if (caption.isNotEmpty)
                            Text(
                              caption,
                              style: const TextStyle(
                                fontSize: 12,
                                color: _muted,
                              ),
                            ),
                        ],
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _badgeRow() => Row(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: _blueSoft,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(_modeIcon('${live['icon']}'), size: 15, color: _blueDeep),
            const SizedBox(width: 6),
            Text(
              '${live['name'] ?? ''}',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: _blueDeep,
              ),
            ),
          ],
        ),
      ),
      if (live['elapsed'] != null) ...[
        const SizedBox(width: 10),
        const Icon(Icons.schedule_rounded, size: 15, color: _faint),
        const SizedBox(width: 4),
        Text(
          '${_clock(_elapsed)} ${running ? '경과' : '걸림'}',
          style: const TextStyle(
            fontSize: 13,
            color: _muted,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
      ],
    ],
  );

  /// 기다리는 동안 6초마다 바뀌는 짧은 안내(지금 하는 일과 관련된 사실).
  Widget _tipCard() {
    final index = _tip % tips.length;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      decoration: BoxDecoration(
        color: const Color(0xfff8fafc),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.lightbulb_outline_rounded, size: 16, color: _blue),
              SizedBox(width: 6),
              Text(
                '알고 계셨나요?',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: _blue,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          AnimatedSwitcher(
            duration: _d(450),
            layoutBuilder: (current, previous) => Stack(
              alignment: Alignment.topLeft,
              children: [...previous, ?current],
            ),
            transitionBuilder: (child, animation) => FadeTransition(
              opacity: animation,
              child: SlideTransition(
                position: Tween(
                  begin: const Offset(0.08, 0),
                  end: Offset.zero,
                ).animate(
                  CurvedAnimation(parent: animation, curve: Curves.easeOut),
                ),
                child: child,
              ),
            ),
            child: Text(
              '${tips[index]}',
              key: ValueKey(index),
              style: const TextStyle(fontSize: 13, color: _ink, height: 1.55),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              for (var i = 0; i < tips.length; i++)
                AnimatedContainer(
                  duration: _d(300),
                  margin: const EdgeInsets.only(right: 4),
                  width: i == index ? 14 : 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: i == index ? _blue : _line,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  // ---- 오른쪽: 단계 타임라인 ----------------------------------------------

  Widget _timeline() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (((doc['total'] as num?)?.toInt() ?? 0) > 1) ...[
        _documentStrip(),
        const SizedBox(height: 16),
      ],
      for (var i = 0; i < steps.length; i++)
        _stepRow(steps[i] as Map, last: i == steps.length - 1),
    ],
  );

  /// 여러 문서를 처리할 때 위에 보이는 문서 점 줄(끝난 문서는 초록, 지금 문서는 파랑으로 늘어남).
  Widget _documentStrip() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        '${doc['name'] ?? ''}',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: _muted,
        ),
      ),
      const SizedBox(height: 8),
      Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          for (final item in queue)
            AnimatedContainer(
              duration: _d(450),
              curve: _spring,
              width: item['state'] == 'active' ? 28 : 10,
              height: 10,
              decoration: BoxDecoration(
                color: switch (item['state']) {
                  'done' => _mintBright,
                  'failed' => _red,
                  'active' => _blue,
                  _ => _line,
                },
                borderRadius: BorderRadius.circular(5),
              ),
            ),
        ],
      ),
    ],
  );

  Widget _stepRow(Map step, {required bool last}) {
    final state = '${step['state']}';
    final active = state == 'active';
    final done = state == 'done';
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 28,
            child: Column(
              children: [
                const SizedBox(height: 12),
                _stepNode(state),
                if (!last)
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: AnimatedContainer(
                        duration: _d(500),
                        width: 2,
                        decoration: BoxDecoration(
                          color: done ? _mintBright : _line,
                          borderRadius: BorderRadius.circular(1),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: AnimatedContainer(
              duration: _d(420),
              curve: Curves.easeOutCubic,
              margin: const EdgeInsets.only(bottom: 6),
              padding: EdgeInsets.symmetric(
                horizontal: 14,
                vertical: active ? 14 : 10,
              ),
              decoration: BoxDecoration(
                color: active ? _blueSoft : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: AnimatedSize(
                duration: _d(420),
                curve: Curves.easeOutCubic,
                alignment: Alignment.topLeft,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AnimatedDefaultTextStyle(
                      duration: _d(300),
                      style: TextStyle(
                        fontFamily: DefaultTextStyle.of(context).style.fontFamily,
                        fontSize: active ? 16 : 14,
                        height: 1.4,
                        fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                        color: active
                            ? _blueDeep
                            : done
                            ? const Color(0xff475569)
                            : const Color(0xff94a3b8),
                      ),
                      child: Text('${step['name']}'),
                    ),
                    if (active && '${step['detail'] ?? ''}'.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        '${step['detail']}',
                        style: const TextStyle(
                          fontSize: 13,
                          color: _muted,
                          height: 1.55,
                        ),
                      ),
                      if (running) ...[
                        const SizedBox(height: 10),
                        _shimmerBar(),
                      ],
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _stepNode(String state) {
    final Widget node = switch (state) {
      'done' => _popIn(
        const CircleAvatar(
          key: ValueKey('done'),
          radius: 12,
          backgroundColor: _mintSoft,
          child: Icon(Icons.check_rounded, size: 15, color: _mint),
        ),
      ),
      'active' => AnimatedBuilder(
        key: const ValueKey('active'),
        animation: _pulse,
        builder: (context, _) {
          final t = Curves.easeInOut.transform(_pulse.value);
          return Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _blue,
              boxShadow: [
                BoxShadow(
                  color: _blue.withValues(alpha: 0.35 * (1 - t)),
                  blurRadius: 0,
                  spreadRadius: 2 + 6 * t,
                ),
              ],
            ),
            child: const Icon(
              Icons.more_horiz_rounded,
              size: 14,
              color: Colors.white,
            ),
          );
        },
      ),
      _ => Container(
        key: const ValueKey('waiting'),
        width: 24,
        height: 24,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: _line, width: 2),
        ),
      ),
    };
    return AnimatedSwitcher(duration: _d(300), child: node);
  }

  /// 지금 단계 카드 안에서 흐르는 얇은 빛 막대(멈춰 보이지 않게).
  Widget _shimmerBar() => ClipRRect(
    borderRadius: BorderRadius.circular(3),
    child: SizedBox(
      height: 4,
      child: AnimatedBuilder(
        animation: _spin,
        builder: (context, _) => CustomPaint(
          size: const Size(double.infinity, 4),
          painter: _ShimmerPainter(_reduceMotion ? 0.5 : _spin.value),
        ),
      ),
    ),
  );

  Widget _popIn(Widget child) => TweenAnimationBuilder<double>(
    tween: Tween(begin: _reduceMotion ? 1 : 0.4, end: 1),
    duration: _d(520),
    curve: Curves.elasticOut,
    builder: (context, scale, inner) =>
        Transform.scale(scale: scale, child: inner),
    child: child,
  );

  // ---- 파일 변환: 대기열 ----------------------------------------------------

  Widget _fileQueue() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Text(
        '${live['message'] ?? ''}',
        style: const TextStyle(fontSize: 13, color: _muted),
      ),
      const SizedBox(height: 12),
      for (final item in queue) _fileRow(item as Map),
    ],
  );

  Widget _fileRow(Map item) {
    final state = '${item['state']}';
    final active = state == 'active';
    final note = '${item['note'] ?? ''}';
    final Widget icon = switch (state) {
      'done' => _popIn(
        const Icon(
          Icons.check_circle_rounded,
          key: ValueKey('done'),
          color: _mintBright,
          size: 22,
        ),
      ),
      'failed' => _popIn(
        const Icon(
          Icons.error_rounded,
          key: ValueKey('failed'),
          color: _red,
          size: 22,
        ),
      ),
      'active' => const SizedBox(
        key: ValueKey('active'),
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2.4, color: _blue),
      ),
      _ => const Icon(
        Icons.schedule_rounded,
        key: ValueKey('waiting'),
        color: _faint,
        size: 20,
      ),
    };
    return AnimatedContainer(
      duration: _d(420),
      curve: Curves.easeOutCubic,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: active ? _blueSoft : const Color(0xfff8fafc),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: active ? _sky : _line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              SizedBox(
                width: 24,
                child: Center(
                  child: AnimatedSwitcher(duration: _d(300), child: icon),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  '${item['name']}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    color: state == 'waiting' ? _faint : _ink,
                  ),
                ),
              ),
              if (state == 'done' && note.isNotEmpty) ...[
                const Icon(Icons.arrow_forward_rounded, size: 14, color: _faint),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    note,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 13, color: _mint),
                  ),
                ),
              ],
            ],
          ),
          if (state == 'failed')
            Padding(
              padding: const EdgeInsets.only(left: 36, top: 6),
              child: Text(
                '${note.isEmpty ? '바꾸지 못했어요' : note} · 원본은 그대로예요',
                style: const TextStyle(fontSize: 12, color: _red),
              ),
            ),
          if (active && running)
            Padding(
              padding: const EdgeInsets.only(left: 36, top: 10),
              child: _shimmerBar(),
            ),
        ],
      ),
    );
  }

  Widget _footer() => Padding(
    padding: const EdgeInsets.only(top: 16),
    child: Align(
      alignment: Alignment.centerLeft,
      child: TextButton.icon(
        onPressed: widget.onShowLog,
        icon: const Icon(Icons.receipt_long_outlined),
        label: const Text('상세 작업 로그'),
      ),
    ),
  );
}

/// 활동 링: 회색 트랙 위에 파랑→하늘 그라데이션 호를 둥근 끝으로 그린다. 끝나면 초록.
class _RingPainter extends CustomPainter {
  _RingPainter({
    required this.value,
    required this.glow,
    required this.spin,
    required this.done,
  });

  final double value;
  final double glow;
  final double? spin;
  final bool done;

  @override
  void paint(Canvas canvas, Size size) {
    const stroke = 16.0;
    final center = size.center(Offset.zero);
    final radius = (size.shortestSide - stroke) / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke
        ..color = const Color(0xffedf2f7),
    );
    final colors = done
        ? const [_mint, _mintBright, _mint]
        : const [_blueDeep, _sky, _blueDeep];
    // 아직 0%면 짧은 호가 돌며 '시작하는 중'임을 보여 준다.
    final start = -math.pi / 2 + (spin ?? 0) * 2 * math.pi;
    final sweep = spin != null
        ? math.pi / 3
        : (value.clamp(0.0, 1.0) * 2 * math.pi);
    if (sweep <= 0) return;
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..shader = SweepGradient(
        colors: colors,
        transform: GradientRotation(start),
      ).createShader(rect);
    canvas.drawArc(rect, start, sweep, false, paint);
    // 끝점의 빛: 작업 중에 숨 쉬듯 커졌다 작아진다.
    if (!done && glow > 0) {
      final end = start + sweep;
      final tip = center + Offset(math.cos(end), math.sin(end)) * radius;
      canvas.drawCircle(
        tip,
        stroke / 2 + 4 * glow,
        Paint()..color = _sky.withValues(alpha: 0.28 * (1 - glow) + 0.08),
      );
    }
  }

  @override
  bool shouldRepaint(_RingPainter old) =>
      old.value != value ||
      old.glow != glow ||
      old.spin != spin ||
      old.done != done;
}

/// 흐르는 빛 막대.
class _ShimmerPainter extends CustomPainter {
  _ShimmerPainter(this.t);

  final double t;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xffdbe7fb));
    final width = size.width * 0.35;
    final left = -width + (size.width + width) * t;
    final rect = Rect.fromLTWH(left, 0, width, size.height);
    canvas.drawRect(
      rect,
      Paint()
        ..shader = LinearGradient(
          colors: [
            _sky.withValues(alpha: 0),
            _blue,
            _sky.withValues(alpha: 0),
          ],
        ).createShader(rect),
    );
  }

  @override
  bool shouldRepaint(_ShimmerPainter old) => old.t != t;
}
