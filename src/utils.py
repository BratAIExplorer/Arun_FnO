"""
Utility functions for F&O Trading Bot
"""

import pytz
from datetime import datetime, time as dtime
from typing import Optional
import logging
from rich.console import Console
from rich.theme import Theme
from rich.logging import RichHandler

# Futuristic Theme Definition
FUTURISTIC_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "signal": "bold green",
    "scanner": "bold cyan",
    "execution": "bold magenta",
    "order": "bold white",
    "timestamp": "dim white",
    "price": "bold white",
    "pnl_profit": "bold green",
    "pnl_loss": "bold red",
    "symbol": "bold cyan"
})

# Global Rich Console
console = Console(theme=FUTURISTIC_THEME)


# IST timezone
IST = pytz.timezone("Asia/Kolkata")


class Colors:
    """ANSI color codes for console output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def green(text):
        return f"{Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def red(text):
        return f"{Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def yellow(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"
    
    @staticmethod
    def bold_green(text):
        return f"{Colors.BOLD}{Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def bold_red(text):
        return f"{Colors.BOLD}{Colors.RED}{text}{Colors.RESET}"



def now_ist() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)


def is_trading_day(dt: Optional[datetime] = None) -> bool:
    """
    Check if given date is a trading day (Mon-Fri)
    
    Parameters:
    -----------
    dt : Optional[datetime]
        Date to check (default: today)
        
    Returns:
    --------
    bool
        True if trading day
    """
    if dt is None:
        dt = now_ist()
    
    # Monday = 0, Sunday = 6
    return dt.weekday() < 5


def get_current_time_ist() -> dtime:
    """Get current time (time only, not datetime)"""
    return now_ist().time()


def setup_logging(log_file: str = "trading_bot.log", level=logging.INFO):
    """
    Setup logging configuration with Rich support
    """
    logging.basicConfig(
        level=level,
        format='%(message)s',
        datefmt="[%X]",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            RichHandler(console=console, rich_tracebacks=True, show_path=False)
        ]
    )
    
    return logging.getLogger("rich")

def print_holographic_banner():
    """Print the high-tech ASCII splash screen"""
    banner = """
    SENTINEL TRADING BOT
    --------------------
    [bold cyan]SYNERGY SYSTEMS - COMMAND INTERFACE v2.0[/bold cyan]
    """
    from rich.panel import Panel
    from rich.align import Align
    console.print(Panel(Align.center(banner), border_style="cyan", box=box.ROUNDED))

# Re-import box inside the function to avoid top-level dependency if needed 
# but we already have rich
from rich import box


def calculate_pnl(entry_price: float, exit_price: float, quantity: int) -> float:
    """
    Calculate P&L for a trade
    
    Parameters:
    -----------
    entry_price : float
        Entry price per unit
    exit_price : float
        Exit price per unit
    quantity : int
        Quantity traded
        
    Returns:
    --------
    float
        P&L in INR
    """
    return (exit_price - entry_price) * quantity


def calculate_pnl_percentage(entry_price: float, exit_price: float) -> float:
    """
    Calculate P&L percentage
    
    Parameters:
    -----------
    entry_price : float
        Entry price
    exit_price : float
        Exit price
        
    Returns:
    --------
    float
        P&L percentage
    """
    if entry_price == 0:
        return 0.0
    
    return ((exit_price - entry_price) / entry_price) * 100


def format_currency(amount: float) -> str:
    """Format amount as Indian currency"""
    return f"Rs {amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2f}%"
