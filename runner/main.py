"""Autonomous Scrum Runner CLI — メインエントリーポイント。

サブコマンド:
  init  - references/ の仕様書から config.yaml を自動生成
  run   - Refinement / Sprint パイプラインを実行
"""

import argparse
import sys
from pathlib import Path


def cmd_init(args, root_dir: Path):
    """init サブコマンド: 仕様書から config.yaml を自動生成する。"""
    from runner.config.config_generator import ConfigGenerator

    generator = ConfigGenerator(root_dir)
    success = generator.run()
    sys.exit(0 if success else 1)


def cmd_run(args, root_dir: Path):
    """run サブコマンド: パイプライン（refinement / sprint）を実行する。"""
    from runner.engine.scrum_runner import ScrumRunner

    runner = ScrumRunner(root_dir)

    print("==================================================")
    print(" 🚀 [Scrum Pipeline] Starting Autonomous Runner")
    print(f" 📌 Phase: {args.phase} | Sprint: {args.sprint}")
    print("==================================================")

    if args.phase in ["all", "refinement"]:
        runner.run_refinement_phase()

    if args.phase in ["all", "sprint"]:
        runner.run_sprint_phase(sprint_num=args.sprint)

    print("==================================================")
    print(" ✨ [Task Complete] Process finished successfully!")
    print("==================================================")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Scrum Runner CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            "  python3 runner/main.py init                  # config.yaml 自動生成\n"
            "  python3 runner/main.py run --phase all        # 全フェーズ実行\n"
            "  python3 runner/main.py run --phase refinement # Refinementのみ\n"
            "  python3 runner/main.py run --phase sprint --sprint 1\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- init サブコマンド ---
    subparsers.add_parser("init", help="references/ の仕様書から config.yaml を自動生成")

    # --- run サブコマンド ---
    run_parser = subparsers.add_parser("run", help="パイプライン実行")
    run_parser.add_argument(
        "--phase", type=str, default="all",
        choices=["all", "refinement", "sprint"],
        help="実行フェーズ (default: all)",
    )
    run_parser.add_argument(
        "--sprint", type=int, default=1,
        help="Sprint番号 (default: 1)",
    )

    # --- 後方互換: サブコマンド無しで --phase を指定した場合 ---
    parser.add_argument("--phase", type=str, default=None, dest="legacy_phase",
                        choices=["all", "refinement", "sprint"], help=argparse.SUPPRESS)
    parser.add_argument("--sprint", type=int, default=1, dest="legacy_sprint", help=argparse.SUPPRESS)

    args = parser.parse_args()
    root_dir = Path(__file__).resolve().parents[1]

    if args.command == "init":
        cmd_init(args, root_dir)
    elif args.command == "run":
        cmd_run(args, root_dir)
    elif args.legacy_phase:
        # 後方互換: python3 runner/main.py --phase refinement
        print("⚠️ [互換モード] 'run' サブコマンドの使用を推奨します: python3 runner/main.py run --phase ...", flush=True)
        args.phase = args.legacy_phase
        args.sprint = args.legacy_sprint
        cmd_run(args, root_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
