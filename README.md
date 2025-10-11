# Guia do Projeto


## Configuração inicial do ambiente

1. Crie um ambiente virtual (`.venv`), instale as dependencias `requirements.txt`
2. Ative seu ambiente virtual (`.venv`).
3. No terminal do ambiente virtual, execute:
   ```bash
   pip install nbstripout
   nbstripout --install

---

## Estrutura e boas práticas

- Registre as dependencias em `requirements.txt` para todos conseguirem rodar o codigo em seus PCs
- Coloque **todos os arquivos de dados** dentro da pasta `dados/`.
- Coloque dentro de `rascunhos/` arquivos que ainda esteja em desenvolvimento ou exploração, assim vc fica mais a vontade
- As pastas `dados/` e `rascunhos/` estão listadas no `.gitignore`.  
  → Nada dentro delas será enviado ao GitHub, permanecendo apenas no seu computador local.
