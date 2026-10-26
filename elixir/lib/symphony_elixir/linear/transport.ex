defmodule SymphonyElixir.Linear.Transport do
  @moduledoc false

  @spec connect_options(String.t(), (String.t() -> String.t() | nil)) ::
          {:ok, keyword()} | {:error, :invalid_linear_proxy}
  def connect_options(endpoint, getenv \\ &System.get_env/1) do
    uri = URI.parse(endpoint)
    proxy = env_value(getenv, "#{uri.scheme}_proxy")

    if is_nil(proxy) or bypass_proxy?(uri, env_value(getenv, "no_proxy")) do
      {:ok, [timeout: 30_000]}
    else
      proxy_options(proxy)
    end
  end

  defp env_value(getenv, name) do
    Enum.find_value([name, String.upcase(name)], fn key ->
      value = getenv.(key)
      if is_binary(value) and String.trim(value) != "", do: String.trim(value)
    end)
  end

  defp proxy_options(value) do
    with {:ok, %URI{scheme: "http", host: host, port: port} = uri} <- URI.new(value),
         true <- is_binary(host) and host != "" and port in 1..65_535,
         true <- uri.path in [nil, "", "/"] and is_nil(uri.query) and is_nil(uri.fragment) do
      options = [timeout: 30_000, proxy: {:http, host, port, []}]

      options =
        if uri.userinfo do
          auth = "Basic " <> Base.encode64(URI.decode(uri.userinfo))
          Keyword.put(options, :proxy_headers, [{"proxy-authorization", auth}])
        else
          options
        end

      {:ok, options}
    else
      _ -> {:error, :invalid_linear_proxy}
    end
  end

  defp bypass_proxy?(_uri, nil), do: false

  defp bypass_proxy?(uri, exclusions) do
    exclusions
    |> String.split(",", trim: true)
    |> Enum.any?(fn entry -> bypass_entry?(uri, String.trim(entry)) end)
  end

  defp bypass_entry?(_uri, "*"), do: true

  defp bypass_entry?(uri, entry) do
    with {:ok, %URI{host: host, port: port, path: path} = rule} <- URI.new("//" <> String.trim_leading(entry, ".")),
         true <- is_binary(host) and host != "" and path in [nil, ""],
         true <- is_nil(rule.userinfo) and is_nil(rule.query) and is_nil(rule.fragment),
         true <- is_nil(port) or port == uri.port do
      destination = String.downcase(uri.host || "")
      host = String.downcase(host)
      destination == host or String.ends_with?(destination, "." <> host)
    else
      _ -> false
    end
  end
end
