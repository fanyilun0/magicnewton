新建一个minersweep-request.py文件用于转门用于调用 magicnewton 的API来玩扫雷游戏：
0. 获取userId：Get https://www.magicnewton.com/portal/api/user 
{
    "data": {
        "id": "12345678-4444-4444-4444-xxxxxxxxx",
        ...,
    }
}
1. start：https://www.magicnewton.com/portal/api/userQuests
POST
{""questId"":""44ec9674-6125-4f88-9e18-8d6d6be8f156"",""metadata"":{""action"":""START"",""difficulty"":""Easy""}}

2. click: https://www.magicnewton.com/portal/api/userQuests
{""questId"":""44ec9674-6125-4f88-9e18-8d6d6be8f156"",""metadata"":{""action"":""CLICK"",""userQuestId"":""e88ed277-d5c3-43b6-b5ff-1ac3f6e47f6d"",""x"":1,""y"":3}}"

click每次传的坐标需要从 boardresolver。py中计算并获取

然后从返回结果中获取新的board：
"{
    ""message"":""Quest completed"",
    ""data"":{
        ""id"":""c39d9dcc-3450-4234-8ae3-4d6592cb3e37"",
        ""userId"":""d13241f7-1c7d-41e2-9624-091b7f640ec1"",
        ""questId"":""44ec9674-6125-4f88-9e18-8d6d6be8f156"",
        ""status"":""PENDING"",
        ""credits"":0,
        ""createdAt"":""2025-05-12T05:56:33.695Z"",
        ""updatedAt"":""2025-05-12T05:56:41.243Z"",
        ""_minesweeper"":{
            ""gameId"":""ead6ba99-6a6d-4778-a06c-7d1aa320e3bd"",
            ""startTime"":""2025-05-12T05:56:33.925Z"",
            ""difficulty"":""Easy"",
            ""tiles"":[
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,1,null,null,null,null,null],
                [null,null,null,null,null,null,1,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null],
                [null,null,null,null,null,null,null,null,null,null]
            ],
            ""exploded"":false,
            ""gameOver"":false
            }}}"

3. 结束状态：如果 gameOver为true则结束