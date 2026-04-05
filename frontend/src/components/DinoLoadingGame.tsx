import { useEffect, useMemo, useRef, useState } from "react";

type ObstacleType = "rock" | "bird";

type Obstacle = {
  id: number;
  type: ObstacleType;
  x: number;
  y: number;
  width: number;
  height: number;
  scored: boolean;
};

const GAME_WIDTH = 920;
const GAME_HEIGHT = 230;
const GROUND_Y = 190;

const DINO_X = 72;
const DINO_WIDTH = 58;
const DINO_HEIGHT = 54;

const BASE_SPEED = 280;
const GRAVITY = 960;

const svgToDataUri = (svg: string): string => {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

const DINO_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='128' height='108' viewBox='0 0 128 108'>
  <defs>
    <linearGradient id='bodyGrad' x1='0' x2='1'>
      <stop offset='0%' stop-color='#34D399'/>
      <stop offset='100%' stop-color='#10B981'/>
    </linearGradient>
  </defs>
  <g>
    <path d='M20 72 L20 45 Q20 26 41 24 L78 24 Q90 24 97 18 Q102 14 109 16 Q113 18 112 24 Q111 31 103 36 L103 53 Q103 66 92 71 L82 74 L81 90 L70 90 L70 76 L53 76 L52 90 L41 90 L41 75 L30 74 Q20 73 20 72 Z' fill='url(#bodyGrad)'/>
    <path d='M18 55 L7 51 L18 47 Z' fill='#34D399'/>
    <circle cx='88' cy='34' r='3.2' fill='#0F172A'/>
    <path d='M94 44 Q89 48 82 47' stroke='#065F46' stroke-width='2.6' fill='none' stroke-linecap='round'/>
    <circle cx='63' cy='17' r='5' fill='#6EE7B7'/>
    <circle cx='74' cy='14' r='4' fill='#6EE7B7'/>
    <rect x='40' y='36' width='6' height='6' rx='2' fill='#6EE7B7' opacity='0.6'/>
    <rect x='56' y='33' width='6' height='6' rx='2' fill='#6EE7B7' opacity='0.6'/>
    <rect x='26' y='59' width='84' height='3' fill='#047857' opacity='0.35'/>
  </g>
</svg>`;

const ROCK_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='96' height='78' viewBox='0 0 96 78'>
  <defs>
    <linearGradient id='rockGrad' x1='0' x2='1'>
      <stop offset='0%' stop-color='#7DD3FC'/>
      <stop offset='100%' stop-color='#38BDF8'/>
    </linearGradient>
  </defs>
  <path d='M10 64 L16 42 L30 30 L50 24 L68 28 L82 41 L86 56 L79 66 Z' fill='url(#rockGrad)' stroke='#0EA5E9' stroke-width='3'/>
  <path d='M24 56 L30 42 L44 36 L58 41 L66 52 L60 60 L37 63 Z' fill='#0EA5E9' opacity='0.35'/>
  <path d='M18 64 L79 66' stroke='#BAE6FD' stroke-width='2' opacity='0.5'/>
</svg>`;

const BIRD_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='116' height='78' viewBox='0 0 116 78'>
  <defs>
    <linearGradient id='birdGrad' x1='0' x2='1'>
      <stop offset='0%' stop-color='#FDE68A'/>
      <stop offset='100%' stop-color='#F59E0B'/>
    </linearGradient>
  </defs>
  <ellipse cx='48' cy='42' rx='26' ry='14' fill='url(#birdGrad)'/>
  <path d='M20 43 Q34 22 48 41' stroke='#FCD34D' stroke-width='6' fill='none' stroke-linecap='round'/>
  <path d='M43 41 Q58 20 76 42' stroke='#FBBF24' stroke-width='6' fill='none' stroke-linecap='round'/>
  <polygon points='73,40 95,45 73,50' fill='#F59E0B'/>
  <circle cx='58' cy='39' r='3.2' fill='#111827'/>
  <path d='M32 53 Q49 60 66 53' stroke='#F59E0B' stroke-width='3' fill='none' opacity='0.5'/>
</svg>`;

export default function DinoLoadingGame() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const spawnTimerRef = useRef<number>(0);

  const dinoYRef = useRef<number>(0);
  const dinoVYRef = useRef<number>(0);
  const groundedRef = useRef<boolean>(true);
  const boostsLeftRef = useRef<number>(1);

  const scoreRef = useRef<number>(0);
  const bestScoreRef = useRef<number>(0);
  const milestoneRef = useRef<number>(0);
  const nextObstacleIdRef = useRef<number>(1);

  const obstaclesRef = useRef<Obstacle[]>([]);
  const starsRef = useRef<Array<{ x: number; y: number; size: number; speed: number }>>([]);
  const gameOverRef = useRef<boolean>(false);

  const audioCtxRef = useRef<AudioContext | null>(null);

  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);

  const sprites = useMemo(() => {
    const dino = new Image();
    const rock = new Image();
    const bird = new Image();

    dino.src = svgToDataUri(DINO_SVG);
    rock.src = svgToDataUri(ROCK_SVG);
    bird.src = svgToDataUri(BIRD_SVG);

    return { dino, rock, bird };
  }, []);

  const ensureAudio = async () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    if (audioCtxRef.current.state === "suspended") {
      await audioCtxRef.current.resume();
    }
  };

  const playTone = (frequency: number, durationMs: number, type: OscillatorType, gain = 0.03, glideTo?: number) => {
    const ctx = audioCtxRef.current;
    if (!ctx) return;

    const osc = ctx.createOscillator();
    const g = ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(frequency, ctx.currentTime);
    if (glideTo) {
      osc.frequency.exponentialRampToValueAtTime(glideTo, ctx.currentTime + durationMs / 1000);
    }

    g.gain.setValueAtTime(0.0001, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(gain, ctx.currentTime + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + durationMs / 1000);

    osc.connect(g);
    g.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + durationMs / 1000 + 0.02);
  };

  const playJumpSfx = () => {
    playTone(380, 90, "square", 0.022, 640);
    setTimeout(() => playTone(510, 60, "triangle", 0.012), 36);
  };

  const playBoostSfx = () => {
    playTone(700, 85, "triangle", 0.028, 1080);
    setTimeout(() => playTone(920, 60, "triangle", 0.018), 52);
  };

  const playHitSfx = () => {
    playTone(180, 190, "sawtooth", 0.042, 100);
    setTimeout(() => playTone(120, 130, "square", 0.028), 58);
  };

  const playPassObstacleSfx = () => {
    playTone(620, 46, "sine", 0.014, 720);
  };

  const playScoreMilestoneSfx = () => {
    playTone(740, 70, "triangle", 0.016, 900);
    setTimeout(() => playTone(920, 75, "triangle", 0.016, 1160), 65);
    setTimeout(() => playTone(1100, 80, "triangle", 0.015, 1320), 130);
  };

  const resetGame = () => {
    obstaclesRef.current = [];
    spawnTimerRef.current = 0;
    scoreRef.current = 0;
    milestoneRef.current = 0;

    dinoYRef.current = 0;
    dinoVYRef.current = 0;
    groundedRef.current = true;
    boostsLeftRef.current = 1;

    gameOverRef.current = false;
    setGameOver(false);
    setScore(0);
  };

  const jump = async () => {
    await ensureAudio();

    if (gameOverRef.current) {
      resetGame();
      playScoreMilestoneSfx();
      return;
    }

    if (groundedRef.current) {
      dinoVYRef.current = -430;
      groundedRef.current = false;
      boostsLeftRef.current = 1;
      playJumpSfx();
      return;
    }

    if (boostsLeftRef.current > 0) {
      // Mid-air boost for repeated Space/ArrowUp presses.
      dinoVYRef.current = Math.min(dinoVYRef.current - 250, -320);
      boostsLeftRef.current -= 1;
      playBoostSfx();
    }
  };

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" || e.code === "ArrowUp") {
        e.preventDefault();
        void jump();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (starsRef.current.length === 0) {
      starsRef.current = Array.from({ length: 90 }).map(() => ({
        x: Math.random() * GAME_WIDTH,
        y: Math.random() * (GROUND_Y - 20),
        size: 0.8 + Math.random() * 2.2,
        speed: 10 + Math.random() * 24,
      }));
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const intersects = (obs: Obstacle, dinoTop: number) => {
      const dLeft = DINO_X + 8;
      const dRight = DINO_X + DINO_WIDTH - 8;
      const dBottom = dinoTop + DINO_HEIGHT;

      const oLeft = obs.x + 4;
      const oRight = obs.x + obs.width - 4;
      const oTop = obs.y + 2;
      const oBottom = obs.y + obs.height - 2;

      return dLeft < oRight && dRight > oLeft && dinoTop < oBottom && dBottom > oTop;
    };

    const spawnObstacle = () => {
      const roll = Math.random();
      if (roll < 0.58) {
        const width = 34 + Math.random() * 18;
        const height = 26 + Math.random() * 14;
        obstaclesRef.current.push({
          id: nextObstacleIdRef.current++,
          type: "rock",
          x: GAME_WIDTH + 16,
          y: GROUND_Y - height,
          width,
          height,
          scored: false,
        });
      } else {
        const width = 44 + Math.random() * 18;
        const height = 28 + Math.random() * 10;
        const birdY = GROUND_Y - 95 - Math.random() * 26;
        obstaclesRef.current.push({
          id: nextObstacleIdRef.current++,
          type: "bird",
          x: GAME_WIDTH + 16,
          y: birdY,
          width,
          height,
          scored: false,
        });
      }
    };

    const draw = (runSpeed: number) => {
      // Deep space background gradient
      const bg = ctx.createLinearGradient(0, 0, 0, GAME_HEIGHT);
      bg.addColorStop(0, "#020617");
      bg.addColorStop(0.55, "#020617");
      bg.addColorStop(1, "#0b1120");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

      // Nebula glow
      ctx.fillStyle = "rgba(59,130,246,0.14)";
      ctx.beginPath();
      ctx.arc(170, 42, 95, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "rgba(168,85,247,0.13)";
      ctx.beginPath();
      ctx.arc(690, 54, 120, 0, Math.PI * 2);
      ctx.fill();

      // Distant planet
      ctx.fillStyle = "rgba(34,211,238,0.18)";
      ctx.beginPath();
      ctx.arc(812, 38, 24, 0, Math.PI * 2);
      ctx.fill();

      // Starfield with parallax motion
      starsRef.current.forEach((star) => {
        star.x -= (star.speed + runSpeed * 0.06) * (1 / 60);
        if (star.x < -2) {
          star.x = GAME_WIDTH + Math.random() * 30;
          star.y = Math.random() * (GROUND_Y - 20);
        }
        ctx.fillStyle = `rgba(226,232,240,${Math.min(1, 0.45 + star.size * 0.22)})`;
        ctx.fillRect(star.x, star.y, star.size, star.size);
      });

      // Ground and scanlines
      ctx.strokeStyle = "rgba(16,185,129,0.56)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, GROUND_Y);
      ctx.lineTo(GAME_WIDTH, GROUND_Y);
      ctx.stroke();

      ctx.strokeStyle = "rgba(16,185,129,0.22)";
      ctx.setLineDash([8, 8]);
      ctx.beginPath();
      ctx.moveTo(0, GROUND_Y + 7);
      ctx.lineTo(GAME_WIDTH, GROUND_Y + 7);
      ctx.stroke();
      ctx.setLineDash([]);

      const dinoTop = GROUND_Y - DINO_HEIGHT - dinoYRef.current;
      if (sprites.dino.complete) {
        ctx.drawImage(sprites.dino, DINO_X, dinoTop, DINO_WIDTH, DINO_HEIGHT);
      } else {
        ctx.fillStyle = "#34D399";
        ctx.fillRect(DINO_X, dinoTop, DINO_WIDTH, DINO_HEIGHT);
      }

      obstaclesRef.current.forEach((obs) => {
        if (obs.type === "rock") {
          if (sprites.rock.complete) {
            ctx.drawImage(sprites.rock, obs.x, obs.y, obs.width, obs.height);
          } else {
            ctx.fillStyle = "#60A5FA";
            ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
          }
        } else if (sprites.bird.complete) {
          ctx.drawImage(sprites.bird, obs.x, obs.y, obs.width, obs.height);
        } else {
          ctx.fillStyle = "#F59E0B";
          ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
        }
      });
    };

    const frame = (timestamp: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp;
      const delta = Math.min((timestamp - lastTimeRef.current) / 1000, 0.04);
      lastTimeRef.current = timestamp;

      const speedBonus = Math.max(0, scoreRef.current - 120) * 0.28;
      const runSpeed = BASE_SPEED + Math.min(speedBonus, 260);

      if (!gameOverRef.current) {
        // Dino physics
        dinoVYRef.current += GRAVITY * delta;
        dinoYRef.current -= dinoVYRef.current * delta;

        if (dinoYRef.current <= 0) {
          dinoYRef.current = 0;
          dinoVYRef.current = 0;
          groundedRef.current = true;
          boostsLeftRef.current = 1;
        }

        obstaclesRef.current = obstaclesRef.current
          .map((obs) => ({ ...obs, x: obs.x - runSpeed * delta }))
          .filter((obs) => obs.x + obs.width > -8);

        spawnTimerRef.current -= delta;
        if (spawnTimerRef.current <= 0) {
          spawnObstacle();
          const difficultyFactor = Math.min(0.3, scoreRef.current / 1200);
          spawnTimerRef.current = 0.86 - difficultyFactor + Math.random() * 0.8;
        }

        const dinoTop = GROUND_Y - DINO_HEIGHT - dinoYRef.current;
        const hit = obstaclesRef.current.some((obs) => intersects(obs, dinoTop));
        if (hit) {
          gameOverRef.current = true;
          setGameOver(true);
          void ensureAudio().then(playHitSfx);
          if (scoreRef.current > bestScoreRef.current) {
            bestScoreRef.current = Math.floor(scoreRef.current);
            setBestScore(bestScoreRef.current);
          }
        } else {
          scoreRef.current += delta * 20;

          obstaclesRef.current.forEach((obs) => {
            if (!obs.scored && obs.x + obs.width < DINO_X) {
              obs.scored = true;
              scoreRef.current += 14;
              void ensureAudio().then(playPassObstacleSfx);
            }
          });

          const rounded = Math.floor(scoreRef.current);
          setScore(rounded);

          const milestone = Math.floor(rounded / 100);
          if (milestone > milestoneRef.current && milestone > 0) {
            milestoneRef.current = milestone;
            void ensureAudio().then(playScoreMilestoneSfx);
          }
        }
      }

      draw(runSpeed);
      rafRef.current = requestAnimationFrame(frame);
    };

    rafRef.current = requestAnimationFrame(frame);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
        void audioCtxRef.current.close();
      }
    };
  }, [sprites]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold">
          Policy analysis in progress... play while loading
        </p>
        <div className="flex items-center gap-3">
          <p className="text-sm font-bold text-emerald-300">Score: {score}</p>
          <p className="text-xs font-semibold text-cyan-300">Best: {bestScore}</p>
        </div>
      </div>

      <div className="relative w-full overflow-hidden rounded-xl border border-border/30 bg-black/30">
        <button
          type="button"
          onClick={() => void jump()}
          className="w-full block active:scale-[0.998] transition-transform"
          aria-label="Space Dino loading game. Press Space, Arrow Up, or tap to jump and boost."
        >
          <canvas
            ref={canvasRef}
            width={GAME_WIDTH}
            height={GAME_HEIGHT}
            className="w-full h-[198px] block"
          />
        </button>

        {gameOver && (
          <div className="absolute inset-0 bg-black/65 backdrop-blur-[1px] flex items-center justify-center p-3">
            <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 px-4 py-3 text-center space-y-2">
              <p className="text-rose-300 font-bold text-sm uppercase tracking-[0.12em]">Game Over</p>
              <p className="text-xs text-rose-100">You hit an obstacle.</p>
              <p className="text-xs text-cyan-200">Score: {score} | Best: {bestScore}</p>
              <button
                type="button"
                onClick={() => void jump()}
                className="mt-1 text-xs px-3 py-1.5 rounded-md border border-cyan-400/35 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/20"
              >
                Restart (Space / Tap)
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span>Jump: Space / Arrow Up / Tap | Mid-air Boost: 1x</span>
        <span>{gameOver ? "Press Space or tap Restart." : "Outer-space run active: bird + rock obstacles."}</span>
      </div>
    </div>
  );
}
