# Workflows

## Run load flow

Natural-language request:

```text
Run load flow.
```

MCP tool:

```text
run_load_flow
```

## Read bus voltages

Natural-language request:

```text
Read bus voltages.
```

MCP tool:

```text
get_bus_voltages
```

## Line N-1 short-circuit capacity study

Natural-language request:

```text
Run a line N-1 three-phase short-circuit capacity study at Bus 5.
```

MCP tool:

```text
run_n_minus_1_line_short_circuit
```

The workflow:

1. Select target bus.
2. Iterate over all calculation-relevant `ElmLne` lines.
3. Set one line out of service.
4. Run `ComShc` for a three-phase short circuit at the target bus.
5. Capture `m:Ikss` and `m:Skss`.
6. Restore the original line status.
7. Export a CSV result file.

Example output:

```text
examples/n_minus_1_short_circuit_bus_5.csv
```
