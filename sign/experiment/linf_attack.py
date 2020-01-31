import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import argparse
from save_image import save_image
from train_model import Net
from train_model import data_process_lisa



def l_inf_pgd(model, X, y, epsilon=1, alpha=1, num_iter=20, randomize=False):
    """ Construct L_inf adversarial examples on the examples X """
    model.eval()
    if randomize:
        delta = torch.rand_like(X, requires_grad=True)
        delta.data = delta.data * 2 * epsilon - epsilon
        delta.data = (delta.data + X ).clamp(0,1)-(X)
    else:
        delta = torch.zeros_like(X, requires_grad=True)
    for t in range(num_iter):
        #print("reach")
        loss = nn.CrossEntropyLoss()(model(X + delta ), y) #rgb to bgr 
        loss.backward()
        
        delta.data = (delta + alpha*delta.grad.detach().sign()).clamp(-epsilon,epsilon)
        delta.data = (delta.data +X ).clamp(0,1)-(X)
        delta.grad.zero_()
    return delta.detach()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument("model", type=str, help="test_model")
    args = parser.parse_args() 

    eps     = [2   , 4   , 8  , 16 , 2   , 4   , 8  , 16 ]
    alpha   = [0.5 , 1   , 2  , 4  , 0.5 , 1   , 2  , 4  ]
    itera   = [7   , 7   , 7  , 7  , 20  , 20  , 20 , 20 ]
    restart = [1   , 1   , 1  , 1  , 1   , 1   , 1  , 1  ]
    
    model = Net() 
    model.load_state_dict(torch.load('../donemodel/'+args.model))
    
    print("test model is ", args.model)
    model.eval()
    batch_size = 40
    dataloaders,dataset_sizes =data_process_lisa(batch_size)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    for i in range(len(eps)):
        correct = 0 
        total = 0 
        torch.manual_seed(12345)
        for data in dataloaders['val']:
            images, labels = data
            images = images.to(device)
            labels = labels.to(device)
            total += labels.size(0)
            
            check_num = torch.zeros([1,labels.size(0)], dtype= torch.uint8,device=device)
            correct_num = torch.zeros([1,labels.size(0)], dtype= torch.uint8,device=device) + restart[i]
            for j in range(restart[i]):
                delta = l_inf_pgd(model, images, labels, eps[i]/255, alpha[i]/255 ,itera[i] ,True)
                with torch.no_grad():
                    model.eval()
                    outputs = model(images + delta)
                    save_image("linf_attack",images+delta)
                    
                    _, predicted = torch.max(outputs.data, 1)
                
                    #print("predicted is ",predicted,"labels are",labels)
                    check_num += (predicted == labels)
                    #print("yes",check_num)
            correct += (correct_num == check_num).sum().item()
            #print("one batch is over, batch size", labels.size(0), "correct predict is " ,(correct_num == check_num).sum().item())

        print("eps is ",eps[i],", alpha is ",alpha[i],", iteration is ",itera[i]," restart is ", restart[i])
        print('Accuracy of the network on the %s test images: %10.5f %%' % (total,100 * correct / total))










