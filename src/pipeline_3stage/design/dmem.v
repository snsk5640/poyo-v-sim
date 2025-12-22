//
// dmem
//


`include "define.vh"

module dmem #(parameter byte_num = 2'b00) (
    input wire clk,
    input wire we,
    input wire [31:0] addr,
    input wire [7:0] wr_data,
    output wire [7:0] rd_data
);

    reg [7:0] mem [0:16383];  // 64KiB(16bitアドレス空間)
    reg [13:0] addr_sync;  // 64KiBを表現するための14bitアドレス(下位2bitはここでは考慮しない)
   
    initial begin
        case (byte_num)
            2'b00: $readmemh("../software/test/data0.hex", mem); // 2'b00: を追加
            2'b01: $readmemh("../software/test/data1.hex", mem); // 2'b01: を追加
            2'b10: $readmemh("../software/test/data2.hex", mem); // 2'b10: を追加
            2'b11: $readmemh("../software/test/data3.hex", mem); // 2'b11: を追加
        endcase
    end
   
    always @(posedge clk) begin
        if (we) mem[addr[15:2]] <= wr_data;  // 書き込みタイミングをクロックと同期することでBRAM化
        addr_sync <= addr[15:2];  // 読み出しアドレス更新をクロックと同期することでBRAM化
    end

    assign rd_data = mem[addr_sync];

endmodule
