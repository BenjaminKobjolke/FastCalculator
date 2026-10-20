# Currency conversion

FastCalculator supports currency amounts as suffixes, such as `100 usd`,
`50 €`, or `20 gbp`. Convert with `in` or `to`, and combine compatible
amounts in expressions:

```
100 usd in eur
50 € + 20 usd
4.992,00 € + 260,00 €
```

Euro is a built-in static unit, so euro-only calculations always work. Other
currencies need an exchange rate. FastCalculator uses the European Central
Bank's daily reference rates, published with EUR as the base currency. Rates
are fetched from the [ECB daily XML feed](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml);
no API key is needed.

## Downloads are off by default

The `currency/download` setting starts as `False`. While downloads are off,
FastCalculator makes no network request and does not use a cached rate. A line
that needs a missing rate shows `currency off: /currency-rates on` (in German,
`Währung aus: /currency-rates on`) in its result row.

Enable downloads by typing `/currency-rates on`. This saves the setting,
loads any cached rates immediately, and requests the latest ECB rates once.
Disable it with `/currency-rates off`; the app drops rates from memory and
reevaluates the document. With no argument, `/currency-rates` toggles the
setting. The setting is saved across restarts.

When downloads are enabled but a rate is not available yet, the result row
shows `no rate yet` (German: `noch kein Kurs`). This can happen while the first
fetch is pending, if the fetch failed with no cache, or when the rate is not in
the ECB publication.

## Offline cache

Successful ECB responses are validated and cached in QSettings with their
publication date. When downloads are enabled at startup, the cached rates are
loaded first for immediate offline use, then one fetch checks for newer rates.
If that request fails, the cached rates remain available. Turning downloads
off keeps the cache but does not load or use it until downloads are enabled
again. There are no automatic retries or polling requests.

## Supported currency words

Currency symbols and names go after the amount. Prefix forms such as `$20` are
not supported; write `20 $` or `20 usd` instead.

| Currency | Accepted suffixes |
|----------|-------------------|
| US dollar | `usd`, `dollar`, `dollars`, `$` |
| Euro | `eur`, `euro`, `euros`, `€` |
| Pound sterling | `gbp`, `£` |
| Japanese yen | `jpy`, `yen`, `¥` |
| Other ECB currencies | `bgn`, `chf`, `cad`, `aud`, `sek`, `nok`, `dkk`, `pln`, `czk`, `huf`, `ron`, `isk`, `hrk`, `try`, `inr`, `brl`, `cny`, `hkd`, `idr`, `ils`, `krw`, `mxn`, `myr`, `nzd`, `php`, `sgd`, `thb`, `zar` |

The ECB may no longer publish a rate for every supported code. Euro remains
available without a rate; other amounts show the appropriate hint until their
rate is available. See [persistent-settings.md](persistent-settings.md) for
the saved settings and [commands.md](commands.md) for the command reference.
