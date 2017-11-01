import torch
import torch.nn as nn
import torch.nn.functional as F
from utils import *

class Generator(nn.Module):
    """docstring for Generator"""
    
    def __init__(self,least_size,max_size,size_step_ratio,smoothing_steps=None,learning_rate=0.1):
        super(Generator, self).__init__()
        self.least_size = least_size
        self.max_size=max_size
        self.size_step_ratio = size_step_ratio
        self.input_dim=least_size
        self.curr_max_size=self.input_dim*self.size_step_ratio
        self.output_dim=None
        self.c_in=1
        self.c_out=self.c_in*2
        self.layer_list=self.init_layers(self.least_size,self.curr_max_size,self.size_step_ratio)
        self.model=self.make_model(self.layer_list)
        self.optimizer=torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.smoothing_factor=0.2
        self.will_be_next_layers=None

    def make_model(self,layers_list):
        model=nn.Sequential(*layers_list)
        return model

    def init_layers(self,least_size,curr_max_size,size_step_ratio):
        l_of_layer=[]
        self.output_dim=self.input_dim*size_step_ratio
        while True:
            if self.output_dim<= curr_max_size:
                k_size=calculate_deconv_kernel_size(self.input_dim,size_step_ratio)
                l_of_layer.append(deconv(self.c_in,self.c_out,k_size))
                self.input_dim=self.input_dim*size_step_ratio
                self.output_dim=self.input_dim*size_step_ratio
                self.c_in=self.c_out
                self.c_out=self.c_in*2
            else:
                break
        return l_of_layer

    def add_layer(self,with_smoothing=False):
        if not with_smoothing:
            if self.output_dim<=self.max_size:
                k_size=calculate_deconv_kernel_size(self.input_dim,self.size_step_ratio) 
                self.layer_list.append(deconv(self.c_in,self.c_out,k_size))
                self.input_dim=self.input_dim*self.size_step_ratio
                self.output_dim=self.input_dim*self.size_step_ratio
                self.c_in=self.c_out
                self.c_out=self.c_in*2
            else:
                print ("MAX SIZE REACHED")
            self.model=self.make_model(self.layer_list)
        else:
            if self.will_be_next_layers==None:
                print ("Smoothing branch not present, kindly call add_smoothing_branch")
                return
            self.model=self.make_model(self.will_be_next_layers)
            self.will_be_next_layers=None

    def add_smoothing_branch(self):
        if self.output_dim<=self.max_size:
            k_size=calculate_deconv_kernel_size(self.input_dim,self.size_step_ratio)
            self.will_be_next_layers=self.layer_list+[deconv(self.c_in,self.c_out,k_size)]
        else:
            print ("MAX SIZE REACHED")
            

    def forward(self,input,with_smoothing=False):
        if with_smoothing:
            if self.will_be_next_layers==None:
                print ("call add_smoothing_branch and run for few epochs and then call add_layer with Smoothing")
            A=F.upsample((1-self.smoothing_factor)*self.model(input),scale_factor=self.size_step_ratio)
            B=self.smoothing_factor*self.make_model(self.will_be_next_layers)(input)
            A=sum(A,[0,1],keepdim=True)
            B=sum(B,[0,1],keepdim=True)
            return (1-self.smoothing_factor)*A + self.smoothing_factor*B 
        else:
            A=sum(self.model(input),[0,1],keepdim=True)
            return A
        
class Discriminator(nn.Module):
    """docstring for Discriminator"""
    def __init__(self,least_size,max_size,size_step_ratio,input_shape,smoothing_steps=None,learning_rate=0.1):
        super(Discriminator, self).__init__()
        self.least_size = least_size
        self.size_step_ratio = size_step_ratio
        self.max_size = max_size
        self.input_dim=self.max_size
        self.curr_least_size=int(self.input_dim*self.size_step_ratio)
        self.output_dim=int(self.input_dim*self.size_step_ratio)
        self.least_size=self.least_size
        self.c_in=input_shape[1]
        self.c_out=input_shape[1]//2
        self.layer_list=self.init_layers()
        self.model=self.make_model(self.layer_list)
        self.optimizer=torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        
    def make_model(self,layers_list,smoothing_steps=None):
        model=None
        if smoothing_steps:
            pass
        else:
            model=nn.Sequential(*layers_list)
        return model

    def init_layers(self):
        l_of_layer=[]
        while True:
            if self.output_dim>= self.curr_least_size:
                k_size=calculate_conv_kernel_size(self.input_dim,self.size_step_ratio)
                l_of_layer.append(conv(self.c_in,self.c_out,k_size))
                self.input_dim=self.input_dim*self.size_step_ratio
                self.output_dim=self.input_dim*self.size_step_ratio
                self.c_in=self.c_out
                self.c_out=self.c_in//2
            else:
                break
        return l_of_layer

    def add_layer(self):
        if self.output_dim>=self.least_size:
            k_size=calculate_conv_kernel_size(self.input_dim,self.size_step_ratio) 
            self.layer_list.append(conv(self.c_in,self.c_out,k_size))
            self.input_dim=self.input_dim*self.size_step_ratio
            self.output_dim=self.input_dim*self.size_step_ratio
            self.c_in=self.c_out
            self.c_out=self.c_in//2
        else:
            print ("Least SIZE REACHED")
        self.model=self.make_model(self.layer_list)

    def forward(self,input):
        return self.model(input)

class PGGAN(object):
    """docstring for PGGAN"""
    def __init__(self, least_size,max_size,size_step_ratio):
        super(PGGAN, self).__init__()
        self.least_size = least_size
        self.size_step_ratio = size_step_ratio
        self.max_size = max_size
        self.G=Generator(least_size,max_size,size_step_ratio)
        self.D=Discriminator(least_size,max_size,size_step_ratio)

    def train(self,num_of_epochs,batch_size):
        pass



