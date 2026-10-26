defmodule SymphonyElixir.Linear.TransportTest do
  use ExUnit.Case, async: false

  import ExUnit.CaptureLog
  alias SymphonyElixir.Linear.{Client, Transport}

  @endpoint "https://api.linear.app/graphql"

  test "an unset or blank proxy preserves direct connections" do
    for env <- [%{}, %{"HTTPS_PROXY" => "  ", "https_proxy" => ""}] do
      assert {:ok, [timeout: 30_000]} = options(@endpoint, env)
    end
  end

  test "HTTPS uses the scheme-specific proxy with lowercase precedence and default port" do
    assert {:ok, [timeout: 30_000, proxy: {:http, "lower.example", 80, []}]} =
             options(@endpoint, %{
               "https_proxy" => "http://lower.example",
               "HTTPS_PROXY" => "http://upper.example:8080",
               "HTTP_PROXY" => "http://wrong.example:8080"
             })

    assert {:ok, [timeout: 30_000, proxy: {:http, "upper.example", 8080, []}]} =
             options(@endpoint, %{"https_proxy" => " ", "HTTPS_PROXY" => "http://upper.example:8080"})

    assert {:ok, [timeout: 30_000]} = options(@endpoint, %{"HTTP_PROXY" => "http://wrong.example"})

    assert {:ok, [timeout: 30_000, proxy: {:http, "http.example", 8080, []}]} =
             options("http://linear.example/graphql", %{"http_proxy" => "http://http.example:8080"})
  end

  test "NO_PROXY bypasses exact hosts, domain suffixes, optional ports and wildcard" do
    for rule <- ["api.linear.app", "linear.app", ".linear.app", "api.linear.app:443", "*"] do
      assert {:ok, [timeout: 30_000]} =
               options(@endpoint, %{"HTTPS_PROXY" => "http://proxy.example:8080", "NO_PROXY" => rule})
    end

    for rule <- ["notlinear.app", "api.linear.app:444", "other.example, linear.app.evil"] do
      assert {:ok, opts} =
               options(@endpoint, %{"HTTPS_PROXY" => "http://proxy.example:8080", "NO_PROXY" => rule})

      assert Keyword.has_key?(opts, :proxy)
    end

    assert {:ok, [timeout: 30_000]} =
             options(@endpoint, %{
               "HTTPS_PROXY" => "http://proxy.example:8080",
               "no_proxy" => " LINEAR.APP ",
               "NO_PROXY" => "other.example"
             })
  end

  test "proxy authentication is confined to CONNECT headers" do
    username = Base.url_encode64(:crypto.strong_rand_bytes(12))
    userinfo = username <> ":" <> Base.url_encode64(:crypto.strong_rand_bytes(12))
    proxy = %URI{scheme: "http", host: "proxy.example", port: 8080, userinfo: userinfo} |> URI.to_string()
    assert {:ok, opts} = options(@endpoint, %{"HTTPS_PROXY" => proxy})
    assert opts[:proxy] == {:http, "proxy.example", 8080, []}
    [{name, value}] = opts[:proxy_headers]
    assert name == "proxy-authorization"
    assert value == "Basic " <> Base.encode64(userinfo)
  end

  test "malformed and unsupported proxies fail closed with a value-free error" do
    for proxy <- [
          "invalid",
          "http://",
          "http://proxy.example:0",
          "http://proxy.example:65536",
          "http://proxy.example:bad",
          "http://proxy.example/path",
          "http://proxy.example?query",
          "https://proxy.example",
          "socks5://proxy.example:1080"
        ] do
      assert {:error, :invalid_linear_proxy} = options(@endpoint, %{"HTTPS_PROXY" => proxy})
    end
  end

  test "the Linear GraphQL transport sends HTTPS CONNECT to the configured proxy" do
    keys = ~w(https_proxy HTTPS_PROXY no_proxy NO_PROXY)
    previous = Map.new(keys, &{&1, System.get_env(&1)})

    on_exit(fn ->
      for {key, value} <- previous do
        if value, do: System.put_env(key, value), else: System.delete_env(key)
      end
    end)

    {:ok, listener} = :gen_tcp.listen(0, [:binary, active: false, ip: {127, 0, 0, 1}, packet: :http_bin])
    on_exit(fn -> :gen_tcp.close(listener) end)
    {:ok, port} = :inet.port(listener)
    for key <- keys, do: System.delete_env(key)
    System.put_env("HTTPS_PROXY", "http://127.0.0.1:#{port}")
    parent = self()

    server =
      Task.async(fn ->
        {:ok, socket} = :gen_tcp.accept(listener, 5_000)
        {:ok, request_line} = :gen_tcp.recv(socket, 0, 2_000)
        send(parent, {:proxy_request, request_line})
        :gen_tcp.send(socket, "HTTP/1.1 502 Bad Gateway\r\ncontent-length: 0\r\n\r\n")
        :gen_tcp.close(socket)
      end)

    capture_log(fn ->
      assert {:error, _} =
               Client.graphql("query { viewer { id } }", %{}, tracker_settings: %{endpoint: "https://linear.example.invalid/graphql", api_key: "test-token"})
    end)

    assert_receive {:proxy_request, {:http_request, "CONNECT", {:scheme, "linear.example.invalid", "443"}, {1, 1}}}, 2_000
    Task.await(server)
  end

  defp options(endpoint, env), do: Transport.connect_options(endpoint, &Map.get(env, &1))
end
