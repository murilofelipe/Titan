# Skill Directive: Leitura de Datasheet (Embarcados)

Como extrair de um datasheet o que o driver/firmware precisa, antes de escrever código.

## 1. Checklist de extração
- **Alimentação**: tensão de operação (min/típica/máx), corrente em cada modo (ativo, sleep, deep-sleep).
- **Interface**: barramento (I2C/SPI/UART), endereço/CS, clock máximo, modo SPI (CPOL/CPHA).
- **Timing**: tempo de power-up, tempo de conversão/resposta, delays obrigatórios entre comandos.
- **Registradores**: mapa de registradores, valores de reset, bits de configuração e de status.
- **Faixas**: limites de temperatura, de entrada analógica, resolução do ADC.

## 2. Saída esperada
Um `docs/hardware/<componente>.md` com: pinagem usada, tabela de registradores relevantes,
sequência de inicialização passo a passo, e os delays com a citação da seção do datasheet.

## 3. Armadilhas comuns
- Endereço I2C 7-bit vs 8-bit (deslocamento de 1 bit).
- Confundir corrente de pico com corrente média no cálculo de consumo.
- Ignorar o tempo mínimo de reset — leitura antes da hora retorna lixo.
- Pull-ups do barramento I2C ausentes na PCB.
