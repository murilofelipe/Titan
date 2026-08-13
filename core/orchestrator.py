from typing import Optional
from core.classifier import classify_work
from core.parser import load_profile, PipelineProfile
from core.state import StateManager, PipelineState, StepStatus
from core.context_loader import load_step_context, format_context_for_prompt


class Orchestrator:
    """Orchestrator engine integrating classifier, parser, state manager, and pipeline execution."""

    def __init__(
        self,
        profiles_dir: str = "profiles",
        state_manager: Optional[StateManager] = None,
        base_dir: str = ".",
    ):
        self.profiles_dir = profiles_dir
        self.state_manager = state_manager if state_manager is not None else StateManager()
        self.base_dir = base_dir

    def run_pipeline(
        self,
        profile_id_or_prompt: str = "data_engineering",
        auto_approve: bool = False,
        resume: bool = False,
        reset: bool = False,
    ) -> PipelineState:
        """Executes a pipeline matching the given profile ID or intent prompt.

        Args:
            profile_id_or_prompt: Profile ID (e.g. 'data_engineering') or intent prompt.
            auto_approve: If True, auto-approve all steps without interactive prompt.
            resume: If True, resume execution from last incomplete step.
            reset: If True, reset profile state before execution.

        Returns:
            PipelineState: Final execution state.
        """
        profile_id = classify_work(profile_id_or_prompt, profiles_dir=self.profiles_dir)
        profile: PipelineProfile = load_profile(profile_id, profiles_dir=self.profiles_dir)

        if reset:
            self.state_manager.reset_state(profile_id)

        if resume and not reset:
            existing_state = self.state_manager.load_state(profile_id)
            if existing_state is not None:
                state = existing_state
                start_index = self.state_manager.get_resume_step(profile_id)
            else:
                state = self.state_manager.initialize_state(profile_id, profile.steps)
                start_index = 0
        else:
            state = self.state_manager.initialize_state(profile_id, profile.steps)
            start_index = 0

        print(f"🚀 Iniciando Pipeline: {profile.name}")
        print(f"📖 Descrição: {profile.description}")
        print("-" * 50)

        for step_index in range(start_index, len(profile.steps)):
            step = profile.steps[step_index]
            step_context = load_step_context(
                step.context_files, base_dir=self.base_dir, step_name=step.name
            )

            artifacts_to_save = {}
            if not step_context.is_empty():
                artifacts_to_save["loaded_context"] = step_context.model_dump()

            self.state_manager.update_step_status(
                profile_id,
                step_index,
                StepStatus.IN_PROGRESS,
                artifacts=artifacts_to_save if artifacts_to_save else None,
            )

            print(f"[{step_index + 1}/{len(profile.steps)}] Etapa: {step.name}")
            print(f"🤖 Agente Recomendado: {step.agent}")
            print(f"📝 Descrição da Tarefa: {step.description}")
            if step.context_files:
                print(f"📂 Arquivos de Contexto: {', '.join(step.context_files)}")
                context_text = format_context_for_prompt(step_context)
                if context_text:
                    print(context_text)
            print(f"🎯 Saída Esperada: {step.expected_output}")
            print("-" * 50)

            if not auto_approve:
                input("Pressione ENTER quando tiver concluído esta etapa com o agente sugerido... ")

            self.state_manager.update_step_status(profile_id, step_index, StepStatus.COMPLETED)

        print("✅ Pipeline concluído com sucesso!")
        return self.state_manager.load_state(profile_id)


