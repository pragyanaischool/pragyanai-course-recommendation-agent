from crewai import Crew, Task, Process
from agents import RecommenderAgents
from llm_client import groq_client
import json

# Load the agent definitions
agents = RecommenderAgents()

# --- Task Definitions ---

class RecommendationTasks:

    def _get_profile_schema(self):
        # A simple way to provide the schema to the LLM
        # In a real app, you'd use Pydantic's schema()
        return """
        {
            "user_id": "string",
            "desired_skills": ["skill1", "skill2"],
            "current_skills": ["skill1", "skill2"],
            "budget_min": "integer",
            "budget_max": "integer",
            "preferred_mode": ["online_live", "offline", "self_paced"],
            "goal": "placement | career_growth | academic",
            "branch": "string (e.g., Electronics Engg)",
            "college": "string (e.g., XYZ Institute)",
            "score_percentile": "integer (0-100)"
        }
        """

    def intake_task(self, agent: agents.intake_agent, user_profile_input: Dict) -> Task:
        """
        Task 1: Process raw input into structured JSON.
        """
        return Task(
            description=f"Parse the following user input into a structured JSON object. Use 'default_user' as the user_id.",
            expected_output=f"A single, valid JSON object matching this schema: {self._get_profile_schema()}",
            agent=agent,
            inputs={"user_input": user_profile_input},
            # We add the user input directly to the task prompt
            instructions=f"""
            User-provided data:
            ---
            {json.dumps(user_profile_input, indent=2)}
            ---
            
            Convert this user input into canonical JSON fields based on the schema.
            - `desired_skills` and `current_skills` should be lists of strings.
            - `budget_min` and `budget_max` must be integers.
            - `preferred_mode` must be a list.
            - `goal` must be one of the allowed values.
            - Set `user_id` to 'default_user'.
            
            Return *only* the valid JSON object.
            """
        )

    def skill_matching_task(self, agent: agents.skill_matching_agent) -> Task:
        """
        Task 2: Get course candidates from the vector store.
        """
        return Task(
            description="Find courses matching the user's desired skills.",
            expected_output="A JSON object: {'skill_matches': [{'course_id': ..., 'title': ..., 'skill_match_score': ...}, ...]}",
            agent=agent,
            # Context comes from the output of the intake_task
            context_task_outputs=True 
        )

    def filtering_task(self, agent: agents.filtering_agent) -> Task:
        """
        Task 3: Filter and rank the candidates.
        """
        return Task(
            description="Apply price, mode, academic, and placement filters to the course candidates.",
            expected_output="A JSON object: {'recommendations': [{'course_id': ..., 'combined_score': ..., 'scores': {...}}, ...]}",
            agent=agent,
            # Context comes from intake_task (profile) and skill_matching_task (candidates)
            context_task_outputs=True 
        )

    def explanation_task(self, agent: agents.explanation_agent) -> Task:
        """
        Task 4: Generate human-readable explanations.
        """
        return Task(
            description="Generate explanations for the top 3 recommendations.",
            expected_output="A final JSON object: {'recommendations': [{'course_id': ..., 'title': ..., 'explanation': ...}, ...]}",
            agent=agent,
            context_task_outputs=True,
            # This task's output will be the final output of the crew
            output_json=True
        )

# --- Crew Definition ---

def create_course_recommender_crew(user_profile_input: Dict):
    """
    Creates and configures the sequential recommendation crew.
    """
    # Instantiate Agents
    intake_agent = agents.intake_agent()
    skill_agent = agents.skill_matching_agent()
    filter_agent = agents.filtering_agent()
    explain_agent = agents.explanation_agent()

    # Instantiate Tasks
    tasks = RecommendationTasks()
    
    # Note: CrewAI's local execution doesn't have a built-in way to pass
    # *different* contexts to *different* tasks easily (e.g., Task 3 needs
    # output from Task 1 and 2).
    # A common pattern is to have the tools themselves pull from context
    # or to make the agents smarter.
    
    # For this skeleton, we'll simplify:
    # 1. Intake Agent creates the profile.
    # 2. Skill Agent gets candidates based on profile.
    # 3. Filtering Agent filters candidates based on profile.
    # 4. Explanation Agent explains the filtered list.
    
    # To make this work, we need to pass the *full context* along.
    # The tools in `tools.py` are designed to accept `profile` and `candidates`
    # as direct arguments, which the agents must learn to pass.
    
    # --- Simplified Task Chain for Sequential Process ---
    # We will combine Skill Matching and Filtering into one task
    # for a simpler sequential flow. The `FilteringTool` already
    # *contains* the `SkillMatchingTool`'s logic (via vector_store).
    
    # Let's redefine the tools and agents for this simpler flow.
    # The `FilteringTool` in tools.py is *already* designed to do this.
    # It takes a profile, finds candidates, and filters them.
    # Let's re-read tools.py...
    
    # Ah, `FilteringTool` takes *candidates* as input.
    # `SkillMatchingTool` creates the candidates.
    # This is correct. The flow should be:
    # Task 1 (Intake) -> profile
    # Task 2 (Skill)  -> candidates (uses profile from context)
    # Task 3 (Filter) -> filtered_recommendations (uses profile AND candidates from context)
    # Task 4 (Explain) -> final_explanations (uses filtered_recommendations from context)

    task1 = tasks.intake_task(intake_agent, user_profile_input)
    task2 = tasks.skill_matching_task(skill_agent)
    task3 = tasks.filtering_task(filter_agent)
    task4 = tasks.explanation_task(explain_agent)

    # Set up the crew
    course_crew = Crew(
        agents=[intake_agent, skill_agent, filter_agent, explain_agent],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        verbose=2,
        manager_llm=groq_client # Use LLaMA 3.1 70B for orchestration
    )
    
    return course_crew
