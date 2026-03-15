from rest_framework.decorators import api_view
from rest_framework.response import Response

from game.observers.rich_logger import create_rich_observer
from game.services.simulator import GameSimulator


@api_view(['GET', 'POST'])
def simulate(request):
    observer = create_rich_observer(enabled=True)
    simulator = GameSimulator(event_observer=observer)
    result = simulator.simulate()
    return Response(result.to_dict())
