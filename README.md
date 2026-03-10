# CodeForge Engine

A distributed backend system for executing and evaluating user-submitted code similar to LeetCode.

## Features

- FastAPI backend
- Redis queue system
- Worker-based submission processing
- Docker sandbox execution
- Multi-language support
- SQLAlchemy database models

## Tech Stack

Python  
FastAPI  
Redis  
Docker  
SQLAlchemy  

## Architecture

User → API → Queue → Worker → Execution → Evaluation
