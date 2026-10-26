# Run with `mise exec -- mix run --no-start workflows/aurelio/preflight.exs`.
# Uses Symphony's own tracker tool binding, never a second raw-token client.
alias SymphonyElixir.{Config, Workflow, Workspace}
alias SymphonyElixir.Codex.DynamicTool

workflow = Path.join(__DIR__, "WORKFLOW.md")
System.put_env("AURELIO_RUNNER", Path.join(__DIR__, "runner.py"))

if is_nil(System.get_env("SYMPHONY_WORKSPACE_ROOT")) do
  System.put_env("SYMPHONY_WORKSPACE_ROOT", Path.expand("~/code/aurelio-symphony-workspaces"))
end

Workflow.set_workflow_file_path(workflow)
{:ok, _} = Application.ensure_all_started(:req)
:ok = Config.validate!()
settings = Config.settings!()
true = settings.tracker.kind == "linear"
true = settings.tracker.project_slug == "aurelio-native-shopify-b2b-store-clean-build-2b55b884582b"
true = settings.tracker.required_labels == ["symphony-dispatch-approved"]
true = settings.agent.max_concurrent_agents == 1
true = "LINEAR_API_KEY" in settings.tracker.secret_environment_names
IO.puts("Workflow scope, dispatch label, concurrency and tracker-secret filtering: PASS")

query = """
{
  viewer { organization { name urlKey } }
  project(id: "2849ae33-d00f-45fd-a4ab-fd277672b529") {
    name
    issues(first: 30) {
      nodes { identifier state { name } labels(first: 20) { nodes { name } } }
      pageInfo { hasNextPage }
    }
  }
}
"""

%{"success" => true, "output" => output} =
  DynamicTool.execute("linear_graphql", %{"query" => query}, DynamicTool.bind())

%{"data" => data} = Jason.decode!(output)
true = data["viewer"]["organization"]["urlKey"] == "workspace-ben"
issues = data["project"]["issues"]["nodes"]
false = data["project"]["issues"]["pageInfo"]["hasNextPage"]
true = length(issues) == 15

eligible =
  Enum.filter(issues, fn issue ->
    issue["state"]["name"] in settings.tracker.active_states and
      Enum.any?(issue["labels"]["nodes"], &(&1["name"] == "symphony-dispatch-approved"))
  end)

[] = eligible
IO.puts("Authenticated Aurelio inventory: 15 issues, zero eligible; PASS")

for states <- [settings.tracker.active_states, settings.tracker.terminal_states] do
  {:ok, found} = SymphonyElixir.Linear.Client.fetch_issues_by_states(states)
  IO.puts("Native Symphony Linear poll #{inspect(states)}: PASS (#{length(found)} issues)")
end

identifier = "AURELIO-PREFLIGHT-#{System.os_time(:millisecond)}"
{:ok, workspace} = Workspace.create_for_issue(identifier)

try do
  true = File.regular?(Path.join(workspace, "AGENTS.md"))

  {"https://github.com/craplets25-jpg/aurelio-trade.git\n", 0} =
    System.cmd("git", ["remote", "get-url", "origin"], cd: workspace)

  {"", 0} = System.cmd("git", ["status", "--porcelain"], cd: workspace)
  {sha, 0} = System.cmd("git", ["rev-parse", "HEAD"], cd: workspace)
  IO.puts("Native workspace creation and after_create checkout: PASS; main #{String.trim(sha)}")
after
  {:ok, _} = Workspace.remove(workspace)
end
