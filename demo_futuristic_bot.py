import time
import random
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.align import Align
from rich.text import Text
from rich.style import Style
from rich.gradient import Gradient
from rich.columns import Columns
from rich.progress import BarColumn, Progress, TextColumn

console = Console()

def create_banner():
    banner_text = """
    ███████╗███╗   ██╗ ██████╗     ██████╗  ██████╗ ████████╗
    ██╔════╝████╗  ██║██╔═══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝
    █████╗  ██╔██╗ ██║██║   ██║    ██████╔╝██║   ██║   ██║   
    ██╔══╝  ██║╚██╗██║██║   ██║    ██╔══██╗██║   ██║   ██║   
    ██║     ██║ ╚████║╚██████╔╝    ██████╔╝╚██████╔╝   ██║   
    ╚═╝     ╚═╝  ╚═══╝ ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   
    [bold cyan]SYNERGY SYSTEMS - HOLOGRAPHIC TRADING INTERFACE v2.0[/bold cyan]
    """
    return Panel(Align.center(banner_text), border_style="cyan", box=box.DOUBLE)

def generate_market_table():
    table = Table(title="Live Market Indices", box=box.ROUNDED, expand=True)
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Price", justify="right", style="white")
    table.add_column("Change %", justify="right")
    table.add_column("RSI", justify="right")
    table.add_column("Trend", justify="center")

    indices = [
        ("NIFTY 50", 21710.85, "+0.45%", 55.4, "[bold green]BULLISH[/bold green]"),
        ("BANK NIFTY", 45820.30, "-0.21%", 48.2, "[bold red]BEARISH[/bold red]"),
        ("FINNIFTY", 20145.15, "+0.12%", 52.1, "[bold green]BULLISH[/bold green]"),
        ("SENSEX", 71500.60, "+0.38%", 54.8, "[bold green]BULLISH[/bold green]"),
        ("INDIA VIX", 14.25, "+2.15%", 42.0, "[bold yellow]NEUTRAL[/bold yellow]"),
    ]

    for sym, price, chg, rsi, trend in indices:
        chg_style = "green" if "+" in chg else "red"
        table.add_row(sym, f"₹{price:,.2f}", f"[{chg_style}]{chg}[/{chg_style}]", str(rsi), trend)
    
    return table

def generate_positions_table():
    table = Table(title="Active War Zones (Positions)", box=box.MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("ID", style="dim")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Type", justify="center")
    table.add_column("Entry", justify="right")
    table.add_column("LTP", justify="right")
    table.add_column("P&L (INR)", justify="right")
    table.add_column("Status", justify="center")

    positions = [
        ("BN_CE_001", "BANKNIFTY", "[bold green]CE[/bold green]", "₹245.00", "₹280.50", "[bold green]+1,775.00[/bold green]", "[cyan]MONITORING[/cyan]"),
    ]

    for p in positions:
        table.add_row(*p)
    
    return table

def generate_quantum_heatmap():
    table = Table(title="⚛️ Quantum Heatmap (Trend Alignment)", box=box.HORIZONTALS, expand=True)
    table.add_column("Index", style="cyan")
    table.add_column("1m", justify="center")
    table.add_column("5m", justify="center")
    table.add_column("15m", justify="center")
    table.add_column("1h", justify="center")
    table.add_column("Strength", style="dim")

    indices = [
        ("NIFTY 50", "[bold green]BULL[/bold green]", "[bold green]BULL[/bold green]", "[bold yellow]NEUT[/bold yellow]", "[bold green]BULL[/bold green]", "85%"),
        ("BANK NIFTY", "[bold red]BEAR[/bold red]", "[bold red]BEAR[/bold red]", "[bold red]BEAR[/bold red]", "[bold yellow]NEUT[/bold yellow]", "92%"),
    ]

    for row in indices:
        table.add_row(*row)
    
    return table

def mock_demo():
    # ... previous mock_demo code ...
    pass

if __name__ == "__main__":
    console.print("\n[bold white on blue]  TOP 1% QUANTUM THEME PREVIEW  [/bold white on blue]\n")
    console.print(create_banner())
    
    # Market Data in a panel
    market_panel = Panel(generate_market_table(), title="[bold cyan]STREAM: MARKET_INTELLIGENCE[/bold cyan]", border_style="cyan")
    
    # Quantum Heatmap in a panel
    quantum_panel = Panel(generate_quantum_heatmap(), title="[bold magenta]ANALYSIS: QUANTUM_ALGO[/bold magenta]", border_style="magenta")
    
    # Side-by-side using Columns
    console.print(market_panel)
    console.print(quantum_panel)
    
    # Active Positions
    console.print(Panel(generate_positions_table(), title="[bold green]EXECUTOR: ACTIVE_WAR_ZONE[/bold green]", border_style="green"))
    
    # Futuristic Log
    console.print("\n[bold white]SYSTEM LOGS[/bold white][dim] ──────────────────────────────────────────────────[/dim]")
    console.print("[dim]10:30:00[/dim] [bold cyan]SCANNER[/bold cyan] [white]Searching for strategy confluence...[/white]")
    console.print("[dim]10:30:05[/dim] [bold green]SIGNAL [/bold green] [bold green]QUANTUM ALIGNMENT DETECTED (85% Strength)[/bold green]")
    console.print("[dim]10:30:06[/dim] [bold magenta]AUDIO  [/bold magenta] [italic white]Sentinal: 'Entry sequence initiated.'[/italic white]")
