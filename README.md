# Prompteus - We help diverse teams keep up with others changes

As companies grow, answering the simple question "What's happening right now?" becomes increasingly hard. Information is spread across tools, projects, and teams, making it difficult to get a clear, high-level view. Weekly status reports and ad-hoc "What's going on?" questions drain developer time and still leave managers digging through GitHub with its barely working search functionality and pretty labour-intensive project management.

Teams need a zero-friction way to surface work done, and answer follow-up questions—all in one place, automatically.

For a deeper description of what we are building, please see our [problem statement](docs/PROBLEM_STATEMENT.md).

## Progress reports

| Week | Frank | Stefan | Wolfgang |
|--------|--------|--------|--------|
| 1 | Shared vision about GitHub summarisation | Shared vision about Books-recommender service | Collaborated on both |

further progress reports starting at week 2 are available [on confluence](https://confluence.aet.cit.tum.de/spaces/DO25WR/pages/258581342/Team+Promptheus)

## Screenshots

TBD

## Architecture of the systems

### High level systems architecture diagram
  
> [!TIP]
> The architecture digagram is [also avaliable as a pdf](docs/components.pdf)

![High level systems architecture diagram](docs/components.png)
  
### Usecase diagram
  
![the usecases we are optimising for](docs/usecase.png)
  
### database layout diagram
  
> [!TIP]
> You can view the DBML diagram interactively here:
<https://www.dbdiagram.io/d/681e071a5b2fc4582fec9d54>

![database layout diagram](docs/dbml_diagram.png)

## Getting Started

To get a local demo environment running, you can run 

```shell
COMPOSE_BAKE=true docker compose up
```

You can now head over to [`https://localhost:3000`](https://localhost:3000) to look at the website.

## Contributing

For contributing, we provide a [docker compose-watch](https://docs.docker.com/compose/how-tos/file-watch/) compatible setup.

```shell
COMPOSE_BAKE=true docker compose watch
```
### Demo Script

For a comprehensive demonstration of the AI-powered GitHub analysis features, you can run the interactive demo script:

```shell
# Make sure the container is up and running
docker compose up --build genai

# Run the demo with your GitHub repository
docker compose exec genai python scripts/demo.py --user <your-username> --repo <owner/repo> --week <YYYY-WXX> --github-token <github_pat_XXXX...>
```

The demo showcases:
- 📥 **GitHub Integration**: Fetch contributions automatically via GitHub API
- 🤖 **AI Summary Generation**: Live streaming summaries of your weekly work 
- 💬 **Interactive Q&A**: Ask questions about your contributions with evidence-based answers
- 📊 **Rich Analytics**: Detailed contribution analysis and insights

**Coming Soon**: Conversational Q&A sessions with context retention and broader insights beyond evidence.

See [`genai/README.md`](genai/README.md) for detailed API documentation and configuration options.
