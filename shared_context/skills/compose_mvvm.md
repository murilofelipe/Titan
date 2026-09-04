# Skill Directive: Android — Jetpack Compose + MVVM + Offline-first

Padrões para apps Android nativos usados nos pipelines Titan.

## 1. Camadas (MVVM + Clean)
- **UI (Compose)**: funções `@Composable` puras, state hoisting, sem lógica de negócio. Preview para todo componente reutilizável.
- **ViewModel**: expõe `StateFlow<UiState>` imutável; recebe eventos via funções. Sem referência a `Context`/`View`.
- **Domain (UseCases)**: regra de negócio, independente de Android framework.
- **Data (Repository)**: única fonte de verdade; decide entre cache local e rede.

## 2. Estado da UI
- Um `data class UiState` por tela com `isLoading`, `data`, `error`.
- Coletar com `collectAsStateWithLifecycle()`.
- Nada de `LiveData` novo; usar `StateFlow`/`SharedFlow`.

## 3. Offline-first
- Room como fonte de verdade; a rede só sincroniza o cache.
- Repository retorna `Flow` do Room e dispara refresh em background.
- Toda escrita local marca `pendingSync`; um `WorkManager` reconcilia quando há rede.
- UI nunca bloqueia esperando a rede — mostra dado local + indicador de sync.

## 4. Testes
- ViewModel: teste de unidade com `Turbine` sobre o `StateFlow`, dispatcher de teste.
- Repository: teste com Room in-memory + fake da API.
- Compose: `createComposeRule()` para os fluxos críticos de tela.
