# Segurança e controle de acesso

## Perfis

O servidor aplica as permissões em todas as consultas, independentemente do que a interface mostra:

- vendedores visualizam somente reuniões associadas ao próprio usuário;
- gerentes visualizam todas as reuniões, consultam a equipe e atribuem análises;
- um vendedor não consegue atribuir uma reunião a outra pessoa;
- uma reunião fora do escopo do usuário é respondida como não encontrada.

## Autenticação

- tokens de sessão são gerados com `secrets.token_urlsafe(32)`;
- o banco armazena somente o hash SHA-256 do token;
- senhas usam PBKDF2-HMAC-SHA256, salt aleatório e 310.000 iterações;
- sessões expiram após oito horas e o logout invalida o token;
- falhas de login usam uma mensagem genérica, sem revelar se o e-mail existe.

O formulário de acesso usa campos semânticos e preenchimento automático compatível com gerenciadores de senha. Em produção, todo o tráfego autenticado deve usar HTTPS e as contas de demonstração devem ser substituídas.

## Referências de implementação

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [W3C — Accessible Authentication](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum)
- [W3C — Technique H100](https://www.w3.org/WAI/WCAG22/Techniques/html/H100)
