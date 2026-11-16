from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.documents import Document
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.tools import ToolException

from entrega_4.agent import _WRITE_AUTHORIZED, _message_text, create_tools
from entrega_4.domain_store import ScoutingStore
from entrega_4.metrics import MetricsStore


class FakeRagChain:
    def invoke(self, payload, config=None):
        return {
            "answer": "El arquero domina el juego aéreo [DOC-006].",
            "retrieved": [
                Document(page_content="Informe del arquero", metadata={"source_id": "DOC-006"})
            ],
            "sources": [
                Document(page_content="Informe del arquero", metadata={"source_id": "DOC-006"})
            ],
        }


def test_message_text_does_not_expose_provider_signature_blocks():
    content = [
        {"type": "text", "text": "Respuesta de scouting."},
        {"type": "text_signature", "signature": "private-provider-data"},
    ]
    assert _message_text(content) == "Respuesta de scouting."


def test_domain_tools_retrieve_read_and_require_write_authorization(tmp_path):
    store = ScoutingStore(tmp_path / "scouting.sqlite3")
    metrics = MetricsStore(tmp_path / "metrics.sqlite3")
    retriever, sensor, actuator = create_tools(store, metrics, rag_chain=FakeRagChain())

    retrieved = retriever.invoke({"consulta": "arquero moderno"})
    assert "DOC-006" in retrieved
    assert sensor.invoke({"jugador": "Lautaro"}) == "[]"

    token = _WRITE_AUTHORIZED.set(True)
    try:
        saved = actuator.invoke({"jugador": "Lautaro", "nota": "Revisar el juego aéreo."})
    finally:
        _WRITE_AUTHORIZED.reset(token)
    assert "ID 1" in saved
    assert "Revisar el juego aéreo." in sensor.invoke({"jugador": "Lautaro"})

    try:
        actuator.invoke({"jugador": "Lautaro", "nota": "Sin autorización."})
    except ToolException as error:
        assert "no pidió explícitamente" in str(error)
    else:
        raise AssertionError("El actuador aceptó una escritura sin autorización.")

    snapshot = metrics.snapshot()
    assert snapshot["herramientas"] == {
        "buscar_informes_scouting": 1,
        "consultar_notas_seguimiento": 2,
        "registrar_nota_seguimiento": 2,
    }
    assert snapshot["bloqueos"] == 1


def _counter_graph(checkpointer):
    def count_turns(state):
        turns = sum(isinstance(message, HumanMessage) for message in state["messages"])
        return {"messages": [AIMessage(content=f"turnos={turns}")]}

    builder = StateGraph(MessagesState)
    builder.add_node("respond", count_turns)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile(checkpointer=checkpointer)


def test_sqlite_conversation_memory_survives_reopen(tmp_path):
    database = str(tmp_path / "memory.sqlite3")
    config = {"configurable": {"thread_id": "persistent-thread"}}

    with SqliteSaver.from_conn_string(database) as checkpointer:
        graph = _counter_graph(checkpointer)
        first = graph.invoke({"messages": [HumanMessage(content="Buscá el arquero.")]}, config)
        assert first["messages"][-1].content == "turnos=1"

    with SqliteSaver.from_conn_string(database) as checkpointer:
        graph = _counter_graph(checkpointer)
        second = graph.invoke({"messages": [HumanMessage(content="¿Y su juego aéreo?")]}, config)
        assert second["messages"][-1].content == "turnos=2"
