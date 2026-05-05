# Conecta Fatec Backend

Backend do Conecta Fatec, uma aplicação de rede social acadêmica desenvolvida para conectar estudantes da Fatec em um ambiente digital colaborativo.

A API é responsável pela lógica de negócio da aplicação, autenticação dos usuários, gerenciamento dos dados e comunicação com o frontend.

## Sobre o projeto

O Conecta Fatec Backend foi desenvolvido com foco em organização, segurança e integração com uma interface desacoplada.

A aplicação fornece os recursos necessários para o funcionamento da plataforma, permitindo o gerenciamento de usuários, perfis, publicações, comentários, curtidas, amizades e comunidades.

Toda a comunicação com o frontend é feita por meio de uma API REST, utilizando autenticação baseada em token para proteger as rotas e controlar o acesso dos usuários.

## Principais funcionalidades

- autenticação de usuários via token
- cadastro e gerenciamento de usuários
- gerenciamento de perfis
- criação e interação com publicações
- sistema de curtidas e comentários
- sistema de amizades
- gerenciamento de comunidades

## Arquitetura

O projeto segue o modelo backend desacoplado, onde a API atua de forma independente do frontend, fornecendo dados e regras de negócio para a aplicação.

Essa abordagem facilita a manutenção, evolução do sistema e integração com diferentes interfaces no futuro.

## Tecnologias utilizadas

- Python
- Django
- Django REST Framework
- JWT
- SQLite / PostgreSQL

## Deploy

Link da API:  
