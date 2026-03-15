from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from game.domain.events import (
    DiceRolled,
    GameEvent,
    GameFinished,
    GameStarted,
    LapCompleted,
    PlayerBankrupted,
    PropertiesReleased,
    PropertyBought,
    PropertyNotBought,
    RentPaid,
)

console = Console()
EventObserver = Callable[[GameEvent], None]


def create_rich_observer(enabled: bool = True) -> EventObserver:
    if not enabled:
        return lambda e: None

    def observe(event: GameEvent) -> None:
        if isinstance(event, GameStarted):
            table = Table(show_header=False)
            table.add_column(style='bold cyan')
            table.add_column(style='white')
            table.add_row('Ordem', ' -> '.join(event.player_order))
            table.add_row('Saldo inicial', str(event.initial_balance))
            console.print(Panel(table, title='[bold cyan]INICIO DO JOGO[/]', border_style='cyan'))
        elif isinstance(event, DiceRolled):
            console.print(
                f'[yellow][DADO][/] Rodada {event.round_num} | [bold]{event.player_name}[/] '
                f'rolou [bold]{event.dice_value}[/] | {event.from_position} -> {event.to_position} | saldo: {event.balance}',
                style='yellow'
            )
        elif isinstance(event, LapCompleted):
            console.print(
                f'[bold blue][VOLTA][/] Rodada {event.round_num} | [bold]{event.player_name}[/] '
                f'completou volta! +{event.bonus} | saldo: {event.balance}',
                style='bold blue'
            )
        elif isinstance(event, PropertyBought):
            console.print(
                f'[green][COMPRA][/] Rodada {event.round_num} | [bold]{event.player_name}[/] '
                f'comprou propriedade {event.property_position} por {event.cost} | saldo: {event.balance_after}',
                style='green'
            )
        elif isinstance(event, PropertyNotBought):
            console.print(
                f'[magenta][NAO COMPROU][/] Rodada {event.round_num} | [bold]{event.player_name}[/] '
                f'nao comprou propriedade {event.property_position} (custo {event.cost}) | motivo: {event.reason}',
                style='magenta'
            )
        elif isinstance(event, RentPaid):
            console.print(
                f'[red][ALUGUEL][/] Rodada {event.round_num} | [bold]{event.tenant_name}[/] '
                f'pagou {event.amount} para [bold]{event.owner_name}[/] (prop {event.property_position}) | saldo: {event.balance_after}',
                style='red'
            )
        elif isinstance(event, PlayerBankrupted):
            console.print(
                f'[bold red][FALENCIA][/] Rodada {event.round_num} | [bold]{event.player_name}[/] '
                f'eliminado com saldo {event.balance}',
                style='bold red'
            )
        elif isinstance(event, PropertiesReleased):
            console.print(
                f'[yellow][LIBERADAS][/] Propriedade {event.property_position} de [bold]{event.bankrupt_player}[/] '
                f'disponivel para compra',
                style='yellow'
            )
        elif isinstance(event, GameFinished):
            table = Table(show_header=False)
            table.add_column(style='bold green')
            table.add_column(style='white')
            table.add_row('Vencedor', event.winner)
            table.add_row('Rodadas', str(event.total_rounds))
            table.add_row('Motivo', event.end_reason)
            console.print(Panel(table, title='[bold green]FIM DO JOGO[/]', border_style='green'))

    return observe
