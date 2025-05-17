local function main()
    local function DumpObject(object)
        Printf("--------------------------------- "..object.Name.." Dump Start ---------------------------------")
        object:Dump()
        
        for _, child in ipairs(object:Children()) do
            if(child ~= nil) then
                if(child.Name ~= nil) then
                    coroutine.yield(0.01)
                    DumpObject(child)
                end
                
            end
        end
        Printf("--------------------------------- "..object.Name.." Dump Finish ---------------------------------")

    end
    DumpObject(Root())
end

return main