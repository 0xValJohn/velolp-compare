# %%
import requests
import pandas as pd
import numpy as np

op_price = 1.30
beefi_api_apy = 'https://api.beefy.finance/apy'
beefi_api_tvl = 'https://api.beefy.finance/tvl'
yearn_api = 'https://api.yexporter.io/v1/chains/10/vaults/all'

# %%
response_apy = requests.get(beefi_api_apy)
data_apy = response_apy.json()
filtered_data_apy = {k: v for k, v in data_apy.items() if 'velodrome' in k}
df_apy = pd.DataFrame(list(filtered_data_apy.items()), columns=['Pair', 'Beefy APY'])
response_tvl = requests.get(beefi_api_tvl)
data_tvl = response_tvl.json()

filtered_data_tvl = {}
for _, nested_dict in data_tvl.items():
    for k, v in nested_dict.items():
        if 'velodrome-' in k:
            filtered_data_tvl[k] = v

df_tvl = pd.DataFrame(list(filtered_data_tvl.items()), columns=['Pair', 'Beefy TVL'])
merged_beefy_df = pd.merge(df_apy, df_tvl, on='Pair', how='inner')
merged_beefy_df['Pair'] = merged_beefy_df['Pair'].str.replace('velodrome-v2-', '', regex=False).str.upper().str.replace('/', '-')
merged_beefy_df['Pair'] = merged_beefy_df['Pair'].str.replace('VELODROME', 'V1', regex=False)
merged_beefy_df

# %%
response = requests.get(yearn_api)
data = response.json()
filtered_data = [vault for vault in data if any("StrategyVelodrome" in strategy['name'] or "yvVelo" in strategy['name'] for strategy in vault['strategies'])]

extracted_data = []
for vault in filtered_data:
    for strategy in vault['strategies']:
        pair_name = strategy['name']
        pair_name = pair_name.replace("StrategyVelodromeFactory-vAMMV2-", "").strip()
        pair_name = pair_name.replace("StrategyVelodromeFactory-sAMMV2-", "").strip()
        pair_name = pair_name.replace("StrategyVelodromeFactory", "V1-").strip()
        pair_name = pair_name.replace("StrategyVelodrome", "V1-").strip()
        pair_name = pair_name.replace("Clonable", "").strip()
        pair_name = pair_name.replace("USDCDOLA", "USDC-DOLA").strip()
        pair_name = pair_name.upper().replace("/", "-")

        extracted_data.append({
            'Pair': pair_name, 
            'Yearn APY': vault['apy']['net_apy'], 
            'Yearn TVL': vault['tvl']['tvl'],
            'Yearn Address': vault['address']
        })

yearn_df = pd.DataFrame(extracted_data)
yearn_df

# %%
merge_df = pd.merge(merged_beefy_df, yearn_df, on='Pair', how='outer')

# %%
# From CMO tx - Careful, many pairs names are inverted

pools = {
  'ALETH-WETH': 2000,  
  'USDC-MAI': 1400,
  'DOLA-ERN': 1400,
  'WETH-LUSD': 1000,
  'USDC-VELO': 1000,
  'USDC-SNX': 1000,
  'USDC-ALUSD': 750,
  'USDC-AGEUR': 500, 
  'WETH-TBTC': 500,
  'USDC-MTA': 500,
  'STERN-ERN': 500,
  'STG-USDC': 500,
  'FRAX-ALUSD': 300,
  'WETH-OP': 300,
  'WSTETH-LDO': 300,
  'WBTC-TBTC': 300,
  'OP-USDC': 300,
  'USDC-DOLA': 300,
  'EXA-WETH': 300, 
  'FRAX-DOLA': 200,
  'ALUSD-MAI': 150,
  'OP-VELO': 150,
  'ALETH-FRXETH': 150,
  'IB-WETH': 150,
  'DOLA-MAI': 150,
  'LUSD-ERN': 150
}

merge_df['OP Boost'] = 0

for index, row in merge_df.iterrows():
    pair = row['Pair']
    if pair in pools:
        merge_df.at[index, 'OP Boost'] = pools[pair]

# %%
merge_df['OP boost/TVL'] = np.where(
    merge_df['OP Boost'] != 0,
    op_price * merge_df['OP Boost'] / merge_df['Yearn TVL'] * 100,
    0
)

# %%
merge_df.to_csv('final_data.csv', index=False)
