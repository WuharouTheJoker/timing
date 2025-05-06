conda create --name rc-gnn python=3.9 -y 
conda activate rc-gnn 
conda install numpy networkx tqdm -y
pip install dgl==1.1.2 -i https://pypi.tuna.tsinghua.edu.cn/simple