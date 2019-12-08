# -*- coding: utf-8 -*-
# @Time    : 2019/8/23 22:00
# @Author  : zhoujun

from __future__ import print_function

import argparse
import os

import anyconfig


def init_args():
    parser = argparse.ArgumentParser(description='DBNet.pytorch')
    parser.add_argument('--config_path', default='config/icdar2015_resnet18_FPN_DBhead_polyLR.yaml', type=str)
    parser.add_argument('--local_rank', dest='local_rank', default=0, type=int, help='Use distributed training')

    args = parser.parse_args()
    return args


def main(config):
    import torch
    from models import get_model, get_loss
    from data_loader import get_dataloader
    from trainer import Trainer
    from post_processing import get_post_processing
    from utils import get_metric
    if torch.cuda.device_count() > 1:
        import torch.distributed as dist
        torch.cuda.set_device(args.local_rank)
        dist.init_process_group(backend='nccl', init_method='env://')
    train_loader = get_dataloader(config['dataset']['train'])
    assert train_loader is not None
    validate_loader = get_dataloader(config['dataset']['validate'])

    criterion = get_loss(config['loss']).cuda()

    model = get_model(config['arch'])

    post_p = get_post_processing(config['post_processing'])
    metric = get_metric(config['metric'])

    trainer = Trainer(config=config,
                      model=model,
                      criterion=criterion,
                      train_loader=train_loader,
                      post_process=post_p,
                      metric_cls=metric,
                      validate_loader=validate_loader)
    trainer.train()


if __name__ == '__main__':
    from utils import parse_config

    args = init_args()
    assert os.path.exists(args.config_path)
    config = anyconfig.load(open(args.config_path, 'rb'))
    if 'base' in config:
        config = parse_config(config)
    os.environ['CUDA_VISIBLE_DEVICES'] = ','.join([str(i) for i in config['trainer']['gpus']])
    main(config)
