# Basic setup
lr=0.01
time_steps=79
batch_size=64
epochs=1000

# General Model params

hidden_size=32

# RNN params

# Encoder params
number_heads=0

# Description for run


for model in "GRU" "LSTM"
  do
    for l in 1 2
      do
        for dense_layer in true false
          do


            layers=$l

            if [ "$dense_layer" = true ]; then
              dense_layer_arg="-dense_layer"
            else
              dense_layer_arg=""
            fi


            description="RNN_sweep_Aarav"

            python LightningTrain.py \
              -layers $layers \
              -model $model \
              -hidden_size $hidden_size \
              -lr $lr \
              -time_steps $time_steps \
              -batch_size $batch_size \
              -epochs $epochs \
              $dense_layer_arg \
              -description $description # Uncomment to save model with description
        done
    done
done