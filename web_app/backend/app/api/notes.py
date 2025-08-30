"""
笔记管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import logging
import json

from app.services.note_service import get_note_service, NoteService
from app.services.auth_service import get_current_user
from app.models.note import (
    NoteUploadRequest, NoteResponse, NoteListRequest, NoteListResponse,
    FileFormat, NoteType
)
from app.models.auth import User

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入
async def get_note_service_dep() -> NoteService:
    return get_note_service()

@router.post("/upload", response_model=NoteResponse)
async def upload_note(
    title: str = Form(..., description="笔记标题"),
    description: str = Form("", description="笔记描述"),
    note_type: str = Form("algorithm", description="笔记类型"),
    file_format: str = Form("txt", description="文件格式"),
    tags: str = Form("[]", description="标签列表(JSON格式)"),
    is_public: bool = Form(False, description="是否公开"),
    extract_entities: bool = Form(True, description="是否抽取实体"),
    file_content: Optional[str] = Form(None, description="直接文本内容"),
    file: Optional[UploadFile] = File(None, description="上传的文件"),
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
):
    """
    上传笔记
    支持直接文本输入或文件上传
    需要用户登录
    """
    try:
        # 解析标签
        try:
            tags_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 处理文件数据
        file_data = None
        if file:
            file_data = await file.read()
            if not file_content:
                # 如果没有直接内容，尝试从文件读取
                try:
                    file_content = file_data.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果不是文本文件，保留二进制数据
                    pass
        
        # 验证输入
        if not file_content and not file_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供文件内容或上传文件"
            )
        
        # 创建请求对象
        request = NoteUploadRequest(
            title=title,
            description=description,
            note_type=NoteType(note_type),
            file_format=FileFormat(file_format),
            tags=tags_list,
            is_public=is_public,
            extract_entities=extract_entities,
            file_content=file_content,
            file_data=file_data
        )
        
        # 上传笔记
        result = await note_service.upload_note(request, current_user['id'])
        
        logger.info(f"用户 {current_user['username']} 成功上传笔记: {title}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传笔记失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )

@router.get("/list", response_model=NoteListResponse)
async def get_user_notes(
    page: int = 1,
    size: int = 20,
    note_type: Optional[str] = None,
    search_query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
):
    """
    获取用户笔记列表
    支持分页、类型筛选和搜索
    """
    try:
        request = NoteListRequest(
            page=page,
            size=size,
            note_type=NoteType(note_type) if note_type else None,
            search_query=search_query
        )
        
        result = await note_service.get_user_notes(current_user['id'], request)
        return result
        
    except Exception as e:
        logger.error(f"获取笔记列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取笔记列表失败: {str(e)}"
        )

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note_detail(
    note_id: str,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
):
    """
    获取笔记详情
    """
    try:
        result = await note_service.get_note_by_id(note_id, current_user['id'])
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取笔记详情失败: {str(e)}"
        )

@router.get("/{note_id}/entities")
async def get_note_entities(
    note_id: str,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
) -> Dict[str, Any]:
    """
    获取笔记的实体抽取结果
    """
    try:
        result = await note_service.get_note_entities(note_id, current_user['id'])
        return result
        
    except Exception as e:
        logger.error(f"获取笔记实体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实体信息失败: {str(e)}"
        )

@router.get("/{note_id}/graph")
async def get_note_graph_integration(
    note_id: str,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
) -> Dict[str, Any]:
    """
    获取笔记实体在知识图谱中的集成情况
    """
    try:
        result = await note_service.get_note_graph_integration(note_id, current_user['id'])
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图谱集成信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图谱集成信息失败: {str(e)}"
        )

@router.post("/{note_id}/extract-entities")
async def extract_note_entities(
    note_id: str,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
) -> Dict[str, Any]:
    """
    重新抽取笔记实体
    """
    try:
        result = await note_service.re_extract_entities(note_id, current_user['id'])
        return {
            "message": "实体重新抽取成功",
            "success": True,
            "entity_count": len(result.get('entities', [])),
            "relation_count": len(result.get('relations', []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新抽取实体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"抽取实体失败: {str(e)}"
        )

@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service_dep)
):
    """
    删除笔记
    """
    try:
        result = await note_service.delete_note(note_id, current_user['id'])
        return {"message": "笔记删除成功", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除笔记失败: {str(e)}"
        )

@router.get("/types/list")
async def get_note_types():
    """
    获取笔记类型列表
    """
    return {
        "note_types": [
            {"value": "algorithm", "label": "算法笔记"},
            {"value": "data_structure", "label": "数据结构笔记"},
            {"value": "problem_solving", "label": "题解笔记"},
            {"value": "theory", "label": "理论笔记"},
            {"value": "general", "label": "通用笔记"}
        ],
        "file_formats": [
            {"value": "txt", "label": "纯文本"},
            {"value": "md", "label": "Markdown"},
            {"value": "pdf", "label": "PDF"},
            {"value": "docx", "label": "Word文档"},
            {"value": "html", "label": "HTML"}
        ]
    }
