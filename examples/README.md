# Examples

`catalogs/`, `tenders/`, and all benchmark records are synthetic. Organization names, identifiers, product records, and commercial details in those directories are invented and must not be treated as real procurement or supplier data.

`ted/` contains a trimmed, attributed snapshot of public procurement data returned by the official TED Search API. It is explicitly documented as public rather than synthetic.

Run the baseline match from the repository root:

```bash
uv run opentradeintel match \
  --tender examples/tenders/sample.json \
  --catalog examples/catalogs/sample.csv
```

See `connectors/minimal.py` for the smallest acquisition/mapping composition expected from a new public procurement connector.
