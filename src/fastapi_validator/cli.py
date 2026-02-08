"""Interface de linha de comando para o fastapi-validator."""

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import NoReturn

from .analyzer import APIAnalyzer, APIScorer, Severity
from .config import load_config
from .reports import HTMLReporter, BadgeGenerator, GitHubAnnotationsReporter, JUnitReporter


class Colors:
    """Códigos de cores ANSI para terminal."""

    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls) -> None:
        """Desabilita cores."""
        cls.RED = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.GREEN = ""
        cls.BOLD = ""
        cls.RESET = ""


def load_app(app_path: str):
    """Carrega uma aplicação FastAPI a partir de uma string module:app."""
    if ":" not in app_path:
        print(f"{Colors.RED}Erro: Formato inválido. Use 'module:app'{Colors.RESET}")
        sys.exit(1)

    module_path, app_name = app_path.rsplit(":", 1)

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        print(f"{Colors.RED}Erro ao importar módulo '{module_path}': {e}{Colors.RESET}")
        sys.exit(1)

    try:
        app = getattr(module, app_name)
    except AttributeError:
        print(f"{Colors.RED}Erro: '{app_name}' não encontrado em '{module_path}'{Colors.RESET}")
        sys.exit(1)

    return app


def format_issue(issue, show_suggestions: bool = True) -> str:
    """Formata um issue para exibição no terminal."""
    severity_colors = {
        Severity.ERROR: Colors.RED,
        Severity.WARNING: Colors.YELLOW,
        Severity.INFO: Colors.BLUE,
    }

    color = severity_colors.get(issue.severity, "")
    severity_str = str(issue.severity).upper()

    parts = [f"{color}[{severity_str}]{Colors.RESET} {issue.rule_id}"]

    if issue.path:
        parts.append(f"\n  Path: {issue.path}")
    if issue.method:
        parts.append(f" ({issue.method})")

    parts.append(f"\n  {issue.message}")

    if show_suggestions and issue.suggestion:
        parts.append(f"\n  {Colors.GREEN}Sugestão: {issue.suggestion}{Colors.RESET}")

    return "".join(parts)


def cmd_analyze(args: argparse.Namespace) -> int:
    """Executa o comando analyze."""
    # Carrega configuração do pyproject.toml como defaults
    config = load_config()

    app = load_app(args.app)

    # CLI args sobrescrevem config do pyproject.toml
    severity_str = args.min_severity or config.min_severity
    min_severity = None
    if severity_str:
        try:
            min_severity = Severity(severity_str)
        except ValueError:
            print(f"{Colors.RED}Severidade inválida: {severity_str}{Colors.RESET}")
            return 1

    if args.exclude:
        exclude_rules = args.exclude.split(",")
    elif config.exclude_rules:
        exclude_rules = config.exclude_rules
    else:
        exclude_rules = None

    analyzer = APIAnalyzer(
        exclude_rules=exclude_rules,
        min_severity=min_severity,
    )
    report = analyzer.analyze(app)

    # Calcula score se necessário
    score = None
    if args.format in ("html", "badge") or args.score or config.score:
        scorer = APIScorer()
        score = scorer.calculate(report)

    output_path = args.output

    if args.format == "json":
        data = report.to_dict()
        if score:
            data["score"] = score.to_dict()
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Relatório JSON salvo em: {output_path}")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.format == "html":
        reporter = HTMLReporter()
        if output_path:
            reporter.save(report, output_path, score, app_title=args.app)
            print(f"Relatório HTML salvo em: {output_path}")
        else:
            print(reporter.generate(report, score, app_title=args.app))

    elif args.format == "junit":
        reporter = JUnitReporter()
        if output_path:
            reporter.save(report, output_path)
            print(f"Relatório JUnit salvo em: {output_path}")
        else:
            print(reporter.generate(report))

    elif args.format == "github":
        reporter = GitHubAnnotationsReporter()
        print(reporter.generate(report))
        if output_path:
            reporter.save_summary(report, output_path)
            print(f"Summary salvo em: {output_path}")

    elif args.format == "badge":
        if not output_path:
            print(f"{Colors.RED}Erro: --output é obrigatório para badges{Colors.RESET}")
            return 1
        generator = BadgeGenerator()
        output_dir = Path(output_path)
        saved = generator.save_all_badges(
            score,
            output_dir,
            error_count=report.error_count,
            warning_count=report.warning_count,
        )
        print(f"Badges salvos em: {output_dir}")
        for path in saved:
            print(f"  - {path.name}")

    else:  # text (default)
        print(f"\n{Colors.BOLD}Análise de API RESTful{Colors.RESET}")
        print("=" * 50)
        print(f"Rotas analisadas: {report.analyzed_routes}")
        print(f"Total de issues: {len(report.issues)}")
        print(
            f"  {Colors.RED}Erros: {report.error_count}{Colors.RESET} | "
            f"{Colors.YELLOW}Warnings: {report.warning_count}{Colors.RESET} | "
            f"{Colors.BLUE}Info: {report.info_count}{Colors.RESET}"
        )

        if score:
            print(f"\n{Colors.BOLD}Score: {score.total_score}/100 ({score.grade.value}){Colors.RESET}")

        print("=" * 50)

        if report.issues:
            print(f"\n{Colors.BOLD}Issues encontrados:{Colors.RESET}\n")
            for issue in report.issues:
                print(format_issue(issue, show_suggestions=not args.no_suggestions))
                print()

        if report.has_errors:
            print(f"\n{Colors.RED}{Colors.BOLD}API tem {report.error_count} erro(s)!{Colors.RESET}")
        elif report.warning_count > 0:
            print(f"\n{Colors.YELLOW}API tem {report.warning_count} warning(s).{Colors.RESET}")
        else:
            print(f"\n{Colors.GREEN}API está em conformidade!{Colors.RESET}")

    return 1 if report.has_errors else 0


def cmd_rules(args: argparse.Namespace) -> int:
    """Executa o comando rules."""
    analyzer = APIAnalyzer()
    rules = analyzer.get_available_rules()

    print(f"\n{Colors.BOLD}Regras disponíveis:{Colors.RESET}\n")

    severity_colors = {
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.BLUE,
    }

    for rule in sorted(rules, key=lambda r: (r["severity"], r["rule_id"])):
        color = severity_colors.get(rule["severity"], "")
        print(f"  {color}{rule['rule_id']}{Colors.RESET}")
        print(f"    {rule['description']}")
        print(f"    Severidade: {rule['severity']}")
        print()

    print(f"Total: {len(rules)} regras")
    return 0


def main() -> NoReturn:
    """Ponto de entrada principal do CLI."""
    parser = argparse.ArgumentParser(
        prog="fastapi-validator",
        description="Validador de APIs FastAPI para conformidade RESTful",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desabilita cores no output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analisa uma aplicação FastAPI",
    )
    analyze_parser.add_argument(
        "app",
        help="Aplicação no formato 'module:app'",
    )
    analyze_parser.add_argument(
        "-o", "--output",
        help="Salvar relatório em arquivo",
    )
    analyze_parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "html", "junit", "github", "badge"],
        default="text",
        help="Formato do relatório (default: text)",
    )
    analyze_parser.add_argument(
        "--score",
        action="store_true",
        help="Exibir score da API",
    )
    analyze_parser.add_argument(
        "--min-severity",
        choices=["error", "warning", "info"],
        help="Severidade mínima para exibir",
    )
    analyze_parser.add_argument(
        "--exclude",
        help="Regras a excluir (separadas por vírgula)",
    )
    analyze_parser.add_argument(
        "--no-suggestions",
        action="store_true",
        help="Não exibir sugestões",
    )

    subparsers.add_parser(
        "rules",
        help="Lista todas as regras disponíveis",
    )

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    if args.command == "analyze":
        sys.exit(cmd_analyze(args))
    elif args.command == "rules":
        sys.exit(cmd_rules(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()