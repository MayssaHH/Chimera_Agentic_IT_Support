using Domain.Tickets;
using Microsoft.EntityFrameworkCore;

namespace Persistence;

public class AppDbContext : DbContext
{
    public DbSet<Ticket> Tickets => Set<Ticket>();
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<Ticket>(e =>
        {
            e.HasKey(x => x.Id);
            e.Property(x => x.Title).IsRequired().HasMaxLength(160);
            e.Property(x => x.Status).HasConversion<string>();
            e.Ignore(x => x.History); // or map as owned if you want to persist it
        });
    }
}