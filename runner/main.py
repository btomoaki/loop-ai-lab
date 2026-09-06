import sys
import argparse
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.engine.scrum_runner import ScrumRunner
from runner.engine.sprint_refinement_engine import SprintRefinementEngine


def main():
    parser = argparse.ArgumentParser(description="Loop AI Lab Autonomous Scrum Runner")
    parser.add_argument("command", choices=["run", "audit"], default="run", nargs="?", help="Command to execute: 'run' (full pipeline) or 'audit' (fast independent audits only)")
    parser.add_argument("--phase", choices=["refinement", "execution", "all"], default="all", help="Target ceremony phase")
    parser.add_argument("--sprint", type=int, default=None, help="Specific sprint index to run (defaults to all sprints)")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically approve human review gate without interactive confirmation")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    config = ProjectConfig.load(root_dir)

    if args.command == "audit":
        print("⚡ [Fast Audit Mode] Running Gemini Independent Audits directly on existing backlogs...", flush=True)
        refinement_engine = SprintRefinementEngine(root_dir, config)
        existing_loops = list((root_dir / "state" / ".evaluator").glob("loop_*"))
        current_attempt = len(existing_loops) + 1
        result = refinement_engine.run_individual_final_audits(attempt=current_attempt)
        
        print("\n" + "=" * 50)
        print(f"🏁 [Fast Audit Summary - Directory: {result['loop_dir'].relative_to(root_dir)}]")
        print(f"  - Loop Attempt Count: #{result['attempt']}")
        print(f"  - Spec Compliance Audit: {'✅ PASS' if result['spec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Security & Ethics Audit: {'✅ PASS' if result['sec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Final Verdict: {'🎉 ALL APPROVED' if result['overall_passed'] else '⚠️ VETO DETECTED (Requires Review)'}")
        print("=" * 50 + "\n")
        return

    runner = ScrumRunner(root_dir=root_dir, config=config)
    if args.phase in ["refinement", "all"]:
        runner.run_refinement_phase(auto_approve=args.yes)
    if args.phase in ["execution", "all"]:
        runner.run_sprint_phase(sprint_num=args.sprint)


if __name__ == "__main__":
    main()
