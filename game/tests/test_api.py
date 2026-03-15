from django.test import SimpleTestCase, Client


class TestSimulateEndpoint(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_endpoint_returns_200(self):
        response = self.client.get('/jogo/simular')
        self.assertEqual(response.status_code, 200)

    def test_response_is_json(self):
        response = self.client.get('/jogo/simular')
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_response_has_vencedor_and_jogadores(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIn('vencedor', data)
        self.assertIn('jogadores', data)

    def test_vencedor_is_string(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIsInstance(data['vencedor'], str)

    def test_jogadores_is_list(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIsInstance(data['jogadores'], list)

    def test_vencedor_in_jogadores_list(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIn(data['vencedor'], data['jogadores'])

    def test_valid_player_names_in_response(self):
        valid_names = ['impulsivo', 'exigente', 'cauteloso', 'aleatorio']
        response = self.client.get('/jogo/simular')
        data = response.json()
        for name in data['jogadores']:
            self.assertIn(name, valid_names)

    def test_four_players_in_ranking(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertEqual(len(data['jogadores']), 4)

    def test_vencedor_is_first_in_list(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertEqual(data['jogadores'][0], data['vencedor'])

    def test_post_also_works(self):
        response = self.client.post('/jogo/simular')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('vencedor', data)
        self.assertIn('jogadores', data)

    def test_vencedor_is_non_empty_string(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIsInstance(data['vencedor'], str)
        self.assertGreater(len(data['vencedor']), 0)

    def test_jogadores_is_non_empty_list(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIsInstance(data['jogadores'], list)
        self.assertGreater(len(data['jogadores']), 0)

    def test_vencedor_contained_in_jogadores(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertIn(data['vencedor'], data['jogadores'])

    def test_jogadores_has_no_duplicates(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertEqual(len(data['jogadores']), len(set(data['jogadores'])))

    def test_jogadores_ordered_by_ranking_vencedor_first(self):
        response = self.client.get('/jogo/simular')
        data = response.json()
        self.assertEqual(data['jogadores'][0], data['vencedor'])
