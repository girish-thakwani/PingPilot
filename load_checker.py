from datasets import load_from_disk

ds = load_from_disk("data/mind2web/test_website")
ax = load_from_disk("data/mind2web_axtree/test_website")

print(ds.column_names)
print(ax.column_names)
print(ds[0].keys())
print(ax[0].keys())