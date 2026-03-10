from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData


def process_agent_data(
    agent_data: AgentData,
) -> ProcessedAgentData:
    """
    Process agent data and classify the state of the road surface.
    Parameters:
        agent_data (AgentData): Agent data that containing accelerometer, GPS, and timestamp.
    Returns:
        processed_data_batch (ProcessedAgentData): Processed data containing the classified state of the road surface and agent data.
    """
    y_accelerometer = agent_data.accelerometer.y
    if y_accelerometer < -1000:
        road_state = "pothole"
    else:
        road_state = "normal"

    return ProcessedAgentData(
        road_state=road_state,
        agent_data=agent_data
    )
