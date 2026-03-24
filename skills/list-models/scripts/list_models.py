from agent_shims.model_parameters import list_models

models = list_models()
if not models:
    print("No models in database.")
else:
    for model in models:
        print(model)
