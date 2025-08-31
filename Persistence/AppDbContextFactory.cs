using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace Persistence;

public class AppDbContextFactory : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<AppDbContext>();

        
        var cs = Environment.GetEnvironmentVariable("EF_DESIGN_TIME_CS")
                 ?? "Host=localhost;Port=5432;Database=itagent;Username=postgres;Password=postgres";
        optionsBuilder.UseNpgsql(cs);


        return new AppDbContext(optionsBuilder.Options);
    }
}