_base_ = [
    '../_base_/datasets/ovis.py',
    '../_base_/models/mask2former_tube_r50_ovis.py',
    '../_base_/default_runtime.py',
    '../_base_/schedules/mask2former_swin_schedules_iter.py',
]


depths = [2, 2, 18, 2]
model=dict(
    fix_backbone=False,
    backbone=dict(
        _delete_=True,
        type='SwinTransformer',
        embed_dims=192,
        depths=depths,
        num_heads=[6, 12, 24, 48],
        window_size=12,
        pretrain_img_size=384,
        mlp_ratio=4,
        qkv_bias=True,
        qk_scale=None,
        drop_rate=0.,
        attn_drop_rate=0.,
        drop_path_rate=0.3,
        patch_norm=True,
        out_indices=(0, 1, 2, 3),
        with_cp=True,
        convert_weights=True,
        frozen_stages=-1,
    ),
    panoptic_head=dict(
        in_channels=[192, 384, 768, 1536]
    ),
)

# load tube_link_vps coco r50
load_from = "https://download.openmmlab.com/mmdetection/v2.0/mask2former/mask2former_swin-l-p4-w12-384-in21k_lsj_16x1_100e_coco-panoptic/mask2former_swin-l-p4-w12-384-in21k_lsj_16x1_100e_coco-panoptic_20220407_104949-d4919c44.pth"

work_dir = 'work_dir/ovis_swin_l_010_2_5k_5k_10k_sample4'

crop_size=(384, 640)

img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375],
    to_rgb=True
)
train_pipeline = [
    dict(type='LoadMultiImagesFromFile', to_float32=True),
    dict(
        type='SeqLoadAnnotations',
        with_bbox=True,
        with_mask=True,
        with_track=True),
    dict(
        type='SeqResizeWithDepth',
        multiscale_mode='value',
        share_params=True,
        img_scale=[(480, 1e6), (512, 1e6), (544, 1e6), (576, 1e6), (608, 1e6), (640, 1e6), (672, 1e6), (704, 1e6), (736, 1e6), (768, 1e6), (800, 1e6)],
        keep_ratio=True
    ),
    dict(type='SeqFlipWithDepth', share_params=True, flip_ratio=0.5),
    dict(type='SeqRandomCropWithDepth', crop_size=crop_size, share_params=True),
    dict(type='SeqNormalizeWithDepth', **img_norm_cfg),
    dict(type='SeqPadWithDepth', size_divisor=32),
    dict(
        type='VideoCollect',
        keys=['img', 'gt_bboxes', 'gt_labels', 'gt_masks', 'gt_instance_ids'],
        reject_empty=True,
        num_ref_imgs=4,
    ),
    dict(type='ConcatVideoReferences'),
    dict(type='SeqDefaultFormatBundle', ref_prefix='ref'),
]

data = dict(
    samples_per_gpu=1,
    workers_per_gpu=2,
    train=dict(
        ref_img_sampler=dict(
            num_ref_imgs=4,
            frame_range=[0, 3],
            filter_key_img=False,
            method='uniform'),
        pipeline=train_pipeline
    ),
    test_dataloader=dict(
        workers_per_gpu=0,
    )
)

lr_config = dict(
    policy='step',
    gamma=0.1,
    by_epoch=False,
    step=[2500, 5000],
    warmup='linear',
    warmup_by_epoch=False,
    warmup_iters=500,
    warmup_ratio=0.001,
)

max_iters = 10000
runner = dict(type='IterBasedRunner', max_iters=max_iters)

# no use following
interval = 5000
workflow = [('train', interval)]
checkpoint_config = dict(
    by_epoch=False, interval=interval, save_last=True, max_keep_ckpts=3
)

# Before 365001th iteration, we do evaluation every 5000 iterations.
# After 365000th iteration, we do evaluation every 368750 iterations,
# which means that we do evaluation at the end of training.
dynamic_intervals = [(max_iters // interval * interval + 1, max_iters)]
evaluation = dict()

"""
g8at configs/video/exp_tubeminvis/ovis_r50_004_tubemin_2_5k_5k_10k_sample4.py work_dir/ovis_r50_010_2_5k_5k_10k_sample4/latest.pth --format-only --eval-options resfile_path='work_dir/ovis_r50_010_2_5k_5k_10k_sample4'
"""
