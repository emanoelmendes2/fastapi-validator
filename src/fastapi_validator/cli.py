"""Interface de linha de comando para o fastapi-validator."""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import NoReturn

from .analyzer import APIAnalyzer, APIScorer, Severity
from .config import load_config
from .reports import (
    BadgeGenerator,
    CSVReporter,
    GitHubAnnotationsReporter,
    HTMLReporter,
    JUnitReporter,
)


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


def _ensure_cwd_in_path() -> None:
    """Garante que o diretório atual está no sys.path."""
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)


def _discover_app() -> str | None:
    """Auto-descobre a aplicação FastAPI no diretório atual."""
    _ensure_cwd_in_path()

    candidates = [
        "main:app",
        "app.main:app",
        "app:app",
        "api:app",
        "api.main:app",
        "src.main:app",
        "src.app.main:app",
    ]

    last_error: Exception | None = None

    for candidate in candidates:
        module_path, app_name = candidate.rsplit(":", 1)
        try:
            module = importlib.import_module(module_path)
            obj = getattr(module, app_name, None)
            if obj is not None:
                from fastapi import FastAPI
                if isinstance(obj, FastAPI):
                    return candidate
        except ImportError as e:
            # Distinguir "módulo não existe" de "erro interno"
            missing = getattr(e, "name", None) or ""
            module_missing = (
                missing == module_path
                or module_path.startswith(missing + ".")
            )
            if module_missing:
                continue
            # Dependência interna faltando
            last_error = e
            print(
                f"{Colors.YELLOW}Encontrado '{candidate}' "
                f"mas falhou ao importar:{Colors.RESET}"
            )
            print(f"  {e}\n")
            continue
        except Exception as e:
            # Módulo encontrado mas falhou ao carregar
            last_error = e
            print(
                f"{Colors.YELLOW}Encontrado '{candidate}' "
                f"mas falhou ao importar:{Colors.RESET}"
            )
            print(f"  {e}\n")
            continue

    if last_error:
        print(
            f"{Colors.YELLOW}Dica: o módulo foi encontrado "
            f"mas tem erros de inicialização.{Colors.RESET}"
        )
        print(
            "Verifique variáveis de ambiente (.env) "
            "e dependências do projeto.\n"
        )

    return None


def load_app(app_path: str):
    """Carrega uma aplicação FastAPI a partir de uma string module:app."""
    _ensure_cwd_in_path()

    if ":" not in app_path:
        print(
            f"{Colors.RED}Erro: Formato inválido. "
            f"Use 'module:app'{Colors.RESET}"
        )
        sys.exit(1)

    module_path, app_name = app_path.rsplit(":", 1)

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        if getattr(e, "name", None) == module_path:
            print(
                f"{Colors.RED}Erro: módulo '{module_path}' "
                f"não encontrado.{Colors.RESET}"
            )
            print(
                "Verifique se está no diretório correto "
                "e o módulo existe."
            )
        else:
            print(
                f"{Colors.RED}Erro ao importar "
                f"'{module_path}': {e}{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}Dica: instale a dependência "
                f"faltante e tente novamente.{Colors.RESET}"
            )
        sys.exit(1)

    try:
        app = getattr(module, app_name)
    except AttributeError:
        print(
            f"{Colors.RED}Erro: '{app_name}' não encontrado "
            f"em '{module_path}'{Colors.RESET}"
        )
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


CATEGORY_NAMES = {
    "naming": "Nomenclatura",
    "http": "HTTP Methods",
    "docs": "Documentação",
    "status": "Status Codes",
    "response": "Response Format",
    "versioning": "Versionamento",
    "security": "Segurança",
    "pagination": "Paginação",
    "error_handling": "Error Handling",
}


def _group_issues_by_category(issues, score=None):
    """Agrupa issues por categoria com nome e score."""
    from ._compat import group_issues_by_category

    groups = group_issues_by_category(issues)
    result = []
    for cat_id, cat_issues in groups:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        cat_score = None
        if score and cat_id in score.categories:
            cat_score = score.categories[cat_id].percentage
        result.append(
            (cat_id, cat_name, cat_score, cat_issues)
        )
    return result


def _print_issues_by_category(
    issues, score=None, show_suggestions=True,
):
    """Exibe issues agrupados por categoria."""
    groups = _group_issues_by_category(issues, score)

    for _cat_id, cat_name, cat_score, cat_issues in groups:
        # Header da categoria
        header = f"{Colors.BOLD}{cat_name}{Colors.RESET}"
        if cat_score is not None:
            if cat_score >= 85:
                sc_color = Colors.GREEN
            elif cat_score >= 70:
                sc_color = Colors.BLUE
            elif cat_score >= 50:
                sc_color = Colors.YELLOW
            else:
                sc_color = Colors.RED
            header += (
                f" {sc_color}"
                f"Nota: {cat_score:.0f}/100"
                f"{Colors.RESET}"
            )
        count = len(cat_issues)
        header += f" ({count} issue{'s' if count != 1 else ''})"

        print(f"\n{'-' * 50}")
        print(f"  {header}")
        print(f"{'-' * 50}")

        for issue in cat_issues:
            print(format_issue(issue, show_suggestions))
            print()


def _is_spec_file(path: str) -> bool:
    """Verifica se o argumento é um arquivo de spec OpenAPI."""
    return path.endswith((".json", ".yaml", ".yml"))


def _analyze_spec(args: argparse.Namespace, config) -> int:
    """Analisa uma spec OpenAPI a partir de arquivo."""
    from .openapi_analyzer import OpenAPIAnalyzer

    try:
        spec = OpenAPIAnalyzer.load_spec(args.app)
    except FileNotFoundError:
        print(f"{Colors.RED}Erro: Arquivo não encontrado: {args.app}{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}Erro ao carregar spec: {e}{Colors.RESET}")
        return 1

    report = OpenAPIAnalyzer.analyze(spec)

    # Resolve fail_under: CLI arg sobrescreve config
    fail_under = args.fail_under if args.fail_under is not None else config.fail_under

    # Calcula score se necessário
    score = None
    needs_score = (
        args.format in ("html", "badge")
        or args.score
        or config.score
        or fail_under is not None
        or args.save_baseline
        or args.baseline
    )
    if needs_score:
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

    elif args.format == "csv":
        reporter = CSVReporter()
        if output_path:
            reporter.save(report, output_path)
            print(f"Relatório CSV salvo em: {output_path}")
        else:
            print(reporter.generate(report))

    elif args.format == "html":
        reporter = HTMLReporter()
        if output_path:
            reporter.save(report, output_path, score, app_title=args.app)
            print(f"Relatório HTML salvo em: {output_path}")
        else:
            print(reporter.generate(report, score, app_title=args.app))

    else:  # text
        print(f"\n{Colors.BOLD}Análise de OpenAPI Spec{Colors.RESET}")
        print("=" * 50)
        print(f"Arquivo: {args.app}")
        print(f"Rotas analisadas: {report.analyzed_routes}")
        print(f"Total de issues: {len(report.issues)}")
        print(
            f"  {Colors.RED}Erros: {report.error_count}{Colors.RESET} | "
            f"{Colors.YELLOW}Warnings: {report.warning_count}{Colors.RESET} | "
            f"{Colors.BLUE}Info: {report.info_count}{Colors.RESET}"
        )

        if score:
            score_val = score.total_score
            grade_val = score.grade.value
            print(
                f"\n{Colors.BOLD}Score: "
                f"{score_val}/100 ({grade_val})"
                f"{Colors.RESET}"
            )

        print("=" * 50)

        if report.issues:
            _print_issues_by_category(
                report.issues, score,
                show_suggestions=not args.no_suggestions,
            )

    # Exibir métricas se solicitado
    if hasattr(args, "metrics") and args.metrics and report.metrics:
        m = report.metrics
        print(f"\n{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}  Métricas de Análise{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        print(f"  Tempo de execução:  {m.execution_time_ms:.2f}ms")
        print(f"  Checks executados:  {m.rules_executed}")
        print(f"  Rotas analisadas:   {m.routes_analyzed}")
        print(f"  Cobertura:          {m.coverage:.1f}%")
        print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")

    # --fix não funciona com spec files (precisa do app)
    if args.fix:
        print(
            f"\n{Colors.YELLOW}Aviso: --fix requer uma app FastAPI, "
            f"não funciona com spec files.{Colors.RESET}"
        )

    # Baseline: salvar
    if args.save_baseline:
        from .baseline import save_baseline
        save_baseline(report, score, args.save_baseline)
        print(f"\n{Colors.GREEN}Baseline salvo em: {args.save_baseline}{Colors.RESET}")

    # Baseline: comparar
    if args.baseline:
        from .baseline import compare_with_baseline, format_comparison, load_baseline
        baseline_data = load_baseline(args.baseline)
        comparison = compare_with_baseline(report, score, baseline_data)
        print(format_comparison(comparison))

    # Quality Gate
    exit_code = 1 if report.has_errors else 0
    if fail_under is not None and score is not None:
        if score.total_score < fail_under:
            print(
                f"\n{Colors.RED}{Colors.BOLD}Quality Gate FALHOU: "
                f"score {score.total_score:.1f}/100 < limite {fail_under}"
                f"{Colors.RESET}"
            )
            exit_code = 1
        else:
            print(
                f"\n{Colors.GREEN}Quality Gate OK: "
                f"score {score.total_score:.1f}/100 >= limite {fail_under}"
                f"{Colors.RESET}"
            )

    return exit_code


def cmd_analyze(args: argparse.Namespace) -> int:
    """Executa o comando analyze."""
    # Carrega configuração do pyproject.toml como defaults
    config = load_config()

    # Auto-discovery se nenhum app foi informado
    if args.app is None:
        print(
            f"{Colors.BOLD}Procurando app FastAPI "
            f"no diretório atual...{Colors.RESET}"
        )
        discovered = _discover_app()
        if discovered is None:
            print(
                f"{Colors.RED}Erro: Nenhuma app FastAPI "
                f"encontrada no diretório atual.{Colors.RESET}"
            )
            print(
                "Tente informar o caminho: "
                "fastapi-validator analyze module:app"
            )
            return 1
        args.app = discovered
        print(
            f"{Colors.GREEN}App encontrada: "
            f"{discovered}{Colors.RESET}\n"
        )

    # Detectar se é um arquivo de spec OpenAPI
    if _is_spec_file(args.app):
        return _analyze_spec(args, config)

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

    if args.include:
        include_rules = args.include.split(",")
    elif config.include_rules:
        include_rules = config.include_rules
    else:
        include_rules = None

    analyzer = APIAnalyzer(
        exclude_rules=exclude_rules,
        include_rules=include_rules,
        min_severity=min_severity,
    )
    report = analyzer.analyze(app)

    # Resolve fail_under: CLI arg sobrescreve config
    fail_under = args.fail_under if args.fail_under is not None else config.fail_under

    # Calcula score se necessário
    score = None
    needs_score = (
        args.format in ("html", "badge")
        or args.score
        or config.score
        or fail_under is not None
        or args.save_baseline
        or args.baseline
    )
    if needs_score:
        scorer = APIScorer()
        score = scorer.calculate(report)

    output_path = args.output

    if args.format == "json":
        data = report.to_dict()
        if score:
            data["score"] = score.to_dict()
        if args.fix and report.issues:
            from .analyzer.autofix import AutoFixer
            fixer = AutoFixer()
            fix_report = fixer.generate_suggestions(app, report.issues)
            data["suggestions"] = fix_report.to_dict()
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

    elif args.format == "csv":
        reporter = CSVReporter()
        if output_path:
            reporter.save(report, output_path)
            print(f"Relatório CSV salvo em: {output_path}")
            if hasattr(args, "metrics") and args.metrics and report.metrics:
                if output_path.endswith(".csv"):
                    metrics_path = output_path.replace(
                        ".csv", "_metrics.csv"
                    )
                else:
                    metrics_path = output_path + "_metrics.csv"
                reporter.save_metrics(report, metrics_path)
                print(f"Métricas CSV salvas em: {metrics_path}")
        else:
            print(reporter.generate(report))

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
            score_val = score.total_score
            grade_val = score.grade.value
            print(
                f"\n{Colors.BOLD}Score: "
                f"{score_val}/100 ({grade_val})"
                f"{Colors.RESET}"
            )

        print("=" * 50)

        if report.issues:
            _print_issues_by_category(
                report.issues, score,
                show_suggestions=not args.no_suggestions,
            )

        if report.has_errors:
            err_count = report.error_count
            print(
                f"\n{Colors.RED}{Colors.BOLD}"
                f"API tem {err_count} erro(s)!"
                f"{Colors.RESET}"
            )
        elif report.warning_count > 0:
            warn_count = report.warning_count
            print(
                f"\n{Colors.YELLOW}"
                f"API tem {warn_count} warning(s)."
                f"{Colors.RESET}"
            )
        else:
            print(f"\n{Colors.GREEN}API está em conformidade!{Colors.RESET}")

    # Exibir métricas se solicitado
    if hasattr(args, "metrics") and args.metrics and report.metrics:
        m = report.metrics
        print(f"\n{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}  Métricas de Análise{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        print(f"  Tempo de execução:  {m.execution_time_ms:.2f}ms")
        print(f"  Regras executadas:  {m.rules_executed}")
        print(f"  Regras OK:          {m.rules_passed}")
        print(f"  Regras com issues:  {m.rules_with_issues}")
        print(f"  Rotas analisadas:   {m.routes_analyzed}")
        print(f"  Cobertura:          {m.coverage:.1f}%")
        if m.issues_by_severity:
            print(f"  Por severidade:     {m.issues_by_severity}")
        if m.issues_by_category:
            print(f"  Por categoria:      {m.issues_by_category}")
        print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")

    # Auto-fix: mostrar sugestões de código
    if args.fix and report.issues:
        from .analyzer.autofix import AutoFixer, format_suggestions_report
        fixer = AutoFixer()
        fix_report = fixer.generate_suggestions(app, report.issues)
        print(format_suggestions_report(fix_report))

    # Baseline: salvar
    if args.save_baseline:
        from .baseline import save_baseline
        save_baseline(report, score, args.save_baseline)
        print(f"\n{Colors.GREEN}Baseline salvo em: {args.save_baseline}{Colors.RESET}")

    # Baseline: comparar
    if args.baseline:
        from .baseline import compare_with_baseline, format_comparison, load_baseline
        baseline_data = load_baseline(args.baseline)
        comparison = compare_with_baseline(report, score, baseline_data)
        print(format_comparison(comparison))

    # Quality Gate
    exit_code = 1 if report.has_errors else 0
    if fail_under is not None and score is not None:
        if score.total_score < fail_under:
            print(
                f"\n{Colors.RED}{Colors.BOLD}Quality Gate FALHOU: "
                f"score {score.total_score:.1f}/100 < limite {fail_under}"
                f"{Colors.RESET}"
            )
            exit_code = 1
        else:
            print(
                f"\n{Colors.GREEN}Quality Gate OK: "
                f"score {score.total_score:.1f}/100 >= limite {fail_under}"
                f"{Colors.RESET}"
            )

    return exit_code


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
        nargs="?",
        default=None,
        help=(
            "Aplicação no formato 'module:app' ou caminho "
            "para spec OpenAPI (.json/.yaml/.yml). "
            "Se omitido, auto-descobre a app no diretório atual."
        ),
    )
    analyze_parser.add_argument(
        "-o", "--output",
        help="Salvar relatório em arquivo",
    )
    analyze_parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "html", "junit", "github", "badge", "csv"],
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
        "--include",
        help="Rodar apenas estas regras (separadas por vírgula)",
    )
    analyze_parser.add_argument(
        "--no-suggestions",
        action="store_true",
        help="Não exibir sugestões",
    )
    analyze_parser.add_argument(
        "--metrics",
        action="store_true",
        help="Exibir métricas de análise",
    )
    analyze_parser.add_argument(
        "--fail-under",
        type=int,
        metavar="SCORE",
        help="Falha se score < valor (ex: --fail-under 80)",
    )
    analyze_parser.add_argument(
        "--fix",
        action="store_true",
        help="Exibir sugestões de código para correção",
    )
    analyze_parser.add_argument(
        "--save-baseline",
        metavar="FILE",
        help="Salvar resultado como baseline JSON",
    )
    analyze_parser.add_argument(
        "--baseline",
        metavar="FILE",
        help="Comparar com baseline anterior",
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
