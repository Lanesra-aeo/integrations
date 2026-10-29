# curl examples

Two shell scripts for trying the endpoint from a terminal. They need `curl` and [`jq`](https://jqlang.org).

```bash
export LANESRA_API_KEY=lns_live_your_key_here
./list-tools.sh
./call-tool.sh get_visibility_overview
./call-tool.sh get_brand_rankings '{"limit":5,"minMentions":1}'
./call-tool.sh explain_metric '{"metric":"shareOfVoice"}'
```

| Script | What it does |
| --- | --- |
| [`list-tools.sh`](list-tools.sh) | Lists the tools your key can use |
| [`call-tool.sh`](call-tool.sh) | Calls one tool with JSON arguments and prints its data. Exits 1 on an HTTP or JSON-RPC error and 2 on a tool error |

If your key reads several projects, add `"project":"<slug>"` to the arguments. `./call-tool.sh list_projects` gives the slugs.
