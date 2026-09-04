# Skill Directive: Modelagem de Domínio (DDD)

Para a fase de DDD, antes de desenhar a arquitetura física. Complementa
`clean_architecture.md`.

## 1. Bounded contexts
- Liste os contextos delimitados e o que cada um é dono (dados + regras).
- Um context map: relação entre contextos (parceria, cliente-fornecedor,
  conformista, anti-corruption layer).
- Regra: uma entidade pertence a exatamente um contexto; os outros referenciam por ID.

## 2. Linguagem ubíqua
- Glossário dos termos do domínio, com a definição do especialista.
- O mesmo termo no código, nos testes, na doc e na conversa. Divergência = bug de modelo.

## 3. Blocos táticos
- **Aggregate**: raiz + invariantes que ela protege; alterações passam pela raiz.
  Mantenha pequeno — referência entre aggregates é por ID, não por objeto.
- **Entity** vs **Value Object**: identidade que persiste vs. definido pelos valores (imutável).
- **Domain Event**: fato relevante do negócio já ocorrido, no passado (`PedidoConfirmado`).
- **Domain Service**: regra que não é de uma entidade só.

## 4. Saída esperada
`docs/domain.md`: contextos + context map, glossário, e os aggregates com suas
invariantes. É o insumo da fase de Arquitetura.
