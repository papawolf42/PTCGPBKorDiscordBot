# PTCGP 봇 시스템 아키텍처 설명

## 1. 파일 구조 및 관계

```mermaid
graph TB
    subgraph "원본 시스템 (현재 실행 중)"
        Poke.py[Poke.py<br/>원본 봇]
        GIST.py[GIST.py<br/>GitHub Gist API]
        GistData[(GitHub Gist<br/>클라우드 데이터)]
        
        Poke.py --> GIST.py
        GIST.py <--> GistData
    end
    
    subgraph "마이그레이션 도구"
        migrate[migrate_to_local.py<br/>일회성 실행]
        migrate --> GIST.py
        migrate --> LocalFile.py
        migrate -.->|데이터 복사| LocalData
    end
    
    subgraph "테스트 시스템"
        Poke_test[Poke_test.py<br/>테스트 봇]
        LocalFileAdapter[LocalFileAdapter.py<br/>GIST 인터페이스 어댑터]
        LocalFile.py[LocalFile.py<br/>로컬 파일 시스템]
        LocalData[(로컬 파일<br/>data/poke_data/)]
        
        Poke_test --> LocalFileAdapter
        LocalFileAdapter --> LocalFile.py
        LocalFile.py <--> LocalData
    end
    
    GistData -.->|마이그레이션<br/>1회만 실행| LocalData
```

## 2. 각 파일의 역할

### **Poke.py (원본)**
- 현재 라이브 서비스 중
- GitHub Gist를 데이터베이스로 사용
- 네트워크를 통해 데이터 읽기/쓰기

### **Poke_test.py (테스트 버전)**
- Poke.py의 복사본
- TEST_MODE=True 플래그 추가
- import 부분만 변경: `import LocalFileAdapter as GIST`
- **Poke_local.py는 존재하지 않음** (혼동이 있었던 것 같습니다)

### **LocalFileAdapter.py**
- GIST.py와 동일한 인터페이스 제공
- 내부적으로 LocalFile.py 사용
- Poke_test.py가 수정 없이 작동하도록 하는 어댑터

### **migrate_to_local.py**
- 일회성 실행 스크립트
- Gist → 로컬 파일로 데이터 복사
- 한 번만 실행하면 됨

## 3. 데이터 흐름

```mermaid
sequenceDiagram
    participant User
    participant Poke.py
    participant GIST.py
    participant GitHub Gist
    participant Poke_test.py
    participant LocalFileAdapter
    participant Local Files
    
    Note over Poke.py, GitHub Gist: 원본 시스템 (라이브)
    User->>Poke.py: !command
    Poke.py->>GIST.py: getData()
    GIST.py->>GitHub Gist: HTTP API Call
    GitHub Gist-->>GIST.py: JSON/TEXT data
    GIST.py-->>Poke.py: Parsed data
    Poke.py-->>User: Response
    
    Note over Poke_test.py, Local Files: 테스트 시스템
    User->>Poke_test.py: !command
    Poke_test.py->>LocalFileAdapter: getData()
    LocalFileAdapter->>Local Files: File Read
    Local Files-->>LocalFileAdapter: File content
    LocalFileAdapter-->>Poke_test.py: Parsed data
    Poke_test.py-->>User: Response
```

## 4. 마이그레이션은 언제 일어나나?

```mermaid
graph LR
    A[GitHub Gist<br/>원본 데이터] -->|migrate_to_local.py<br/>실행 시 1회만| B[로컬 파일<br/>data/poke_data/]
    
    B -->|Poke_test.py 실행 중| B
    A -->|Poke.py 실행 중| A
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#9f9,stroke:#333,stroke-width:2px
```

### **마이그레이션 타이밍**:
1. `migrate_to_local.py`를 실행할 때 **1회만** 발생
2. Poke_test.py 실행 중에는 마이그레이션 없음 (로컬 파일만 사용)
3. Poke.py는 여전히 Gist 사용 (마이그레이션과 무관)

## 5. 실제 사용 시나리오

```mermaid
stateDiagram-v2
    [*] --> 현재상태: Poke.py 실행 중
    
    현재상태 --> 마이그레이션: python migrate_to_local.py
    마이그레이션 --> 테스트준비: 데이터 복사 완료
    
    테스트준비 --> 병렬실행: python Poke_test.py
    
    병렬실행 --> 병렬실행: 두 봇 동시 실행
    note right of 병렬실행
        - Poke.py: Gist 사용 (라이브)
        - Poke_test.py: 로컬 파일 사용 (테스트)
    end note
    
    병렬실행 --> 전환완료: 테스트 성공 시
    전환완료 --> [*]: Poke.py를 Poke_test.py로 교체
```

## 6. 장단점 비교

| 항목 | Poke.py (원본) | Poke_test.py (테스트) |
|------|----------------|----------------------|
| 데이터 저장 | GitHub Gist | 로컬 파일 |
| 네트워크 의존성 | 있음 | 없음 |
| API 제한 | 있음 (시간당 5000회) | 없음 |
| 속도 | 느림 (네트워크 지연) | 빠름 (로컬 I/O) |
| 백업 | GitHub가 관리 | 수동 백업 필요 |
| 동시 접근 | API가 처리 | 파일 잠금 필요 |

## 7. 데이터 동기화

```
주의: 마이그레이션 후에는 데이터가 분리됩니다!

Poke.py가 Gist에 쓴 새 데이터 → Poke_test.py는 모름
Poke_test.py가 로컬에 쓴 데이터 → Poke.py는 모름

필요시 재마이그레이션 또는 수동 동기화 필요
```

## 8. MCP 도구 추천

시스템 구조를 더 잘 이해하고 관리하기 위한 도구들:

1. **Mermaid** (위에서 사용 중)
   - 다이어그램을 코드로 작성
   - GitHub, VS Code에서 바로 렌더링

2. **PlantUML**
   - 더 복잡한 UML 다이어그램
   - 시퀀스, 클래스, 컴포넌트 다이어그램

3. **Draw.io (diagrams.net)**
   - 웹 기반 무료 다이어그램 도구
   - 실시간 협업 가능

4. **Excalidraw**
   - 손그림 스타일의 다이어그램
   - 빠른 스케치에 유용

이 문서의 Mermaid 다이어그램은 VS Code의 Markdown Preview Enhanced 확장이나 GitHub에서 바로 볼 수 있습니다!