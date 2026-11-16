from entrega_4.metrics import MetricsStore


def test_metrics_persist_percentiles_tools_blocks_and_costs(tmp_path):
    store = MetricsStore(tmp_path / "metrics.sqlite3")
    store.record_request(
        10,
        input_tokens=100,
        output_tokens=20,
        estimated_cost_usd=0.001,
    )
    store.record_request(
        20,
        is_error=True,
        is_blocked=True,
        estimated_cost_usd=0.002,
    )
    store.record_tool("buscar_informes_scouting")
    store.record_block()

    snapshot = MetricsStore(tmp_path / "metrics.sqlite3").snapshot()
    assert snapshot["consultas"] == 2
    assert snapshot["errores"] == 1
    assert snapshot["bloqueos"] == 2
    assert snapshot["latencia_promedio_ms"] == 15
    assert snapshot["latencia_p95_ms"] == 20
    assert snapshot["herramientas"] == {"buscar_informes_scouting": 1}
    assert snapshot["tokens_entrada"] == 100
    assert snapshot["tokens_salida"] == 20
    assert snapshot["costo_estimado_usd"] == 0.003
