from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.models import Agent, AgentPermission, Policy, SecurityEvent, Tool, ToolCall, User
from app.models.base import Base


def test_schema_supports_basic_create_and_read() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        user = User(email="owner@example.test", display_name="Demo Owner")
        agent = Agent(owner=user, name="Demo Agent", system_prompt="Use only approved tools")
        tool = Tool(name="get_customer", description="Demo lookup", input_schema={"type": "object"})
        permission = AgentPermission(agent=agent, tool=tool, allowed=True)
        call = ToolCall(
            agent=agent,
            request_id="test-request",
            tool_name="get_customer",
            arguments={"customer_id": "1002"},
        )
        event = SecurityEvent(tool_call=call, event_type="demo", severity="low", message="test")
        policy = Policy(name="Demo policy", rules={"allow": ["get_customer"]})
        session.add_all([user, agent, tool, permission, call, event, policy])
        session.commit()

        stored = session.scalar(select(User).where(User.email == "owner@example.test"))
        assert stored is not None
        assert stored.display_name == "Demo Owner"
        assert session.scalar(select(ToolCall).where(ToolCall.tool_name == "get_customer"))
        assert session.scalar(select(SecurityEvent).where(SecurityEvent.severity == "low"))

    engine.dispose()


def test_user_delete_uses_database_cascade() -> None:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="delete@example.test", display_name="Delete Me")
        user.agents.append(Agent(name="Disposable", system_prompt="Demo"))
        session.add(user)
        session.commit()
        session.delete(user)
        session.commit()
        assert session.scalar(select(Agent).where(Agent.name == "Disposable")) is None

    engine.dispose()
